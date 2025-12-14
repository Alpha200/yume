import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar
from uuid import uuid4

from pydantic import BaseModel

from agents import Agent
from agents.lifecycle import AgentHooks
from agents.items import ItemHelpers, ModelResponse, TResponseInputItem
from agents.run_context import RunContextWrapper
from agents.tool import Tool

from components.timezone_utils import now_user_tz
from services.interaction_tracker import interaction_tracker

logger = logging.getLogger(__name__)

TUpdateResult = TypeVar("TUpdateResult")


@dataclass
class InteractionTrackingContext:
    """Payload attached to Runner.run() so the hooks can attach metadata."""

    input_data: str
    agent_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    context_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class _ToolUsageRecord:
    tool_name: str
    start_time: datetime
    input: Optional[str] = None
    end_time: Optional[datetime] = None
    result: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "start_time": self.start_time.isoformat(),
            "input": self.input,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result,
        }


@dataclass
class _InteractionSession:
    context_id: str
    agent_type: str
    input_data: str
    metadata: Dict[str, Any]
    system_instructions: Optional[str]
    start_time: datetime
    last_updated: datetime
    tool_calls: List[_ToolUsageRecord] = field(default_factory=list)
    completed: bool = False


def _serialize_output(output: Any) -> str:
    if output is None:
        return ""
    if isinstance(output, BaseModel):
        return json.dumps(output.model_dump(), default=str)
    if is_dataclass(output):
        return json.dumps(asdict(output), default=str)
    try:
        return str(output)
    except Exception:
        return json.dumps({"value": repr(output)}, default=str)


def _render_input_items(items: list[TResponseInputItem]) -> str:
    serialized_items: List[str] = []
    for item in items:
        if isinstance(item, dict):
            try:
                serialized_items.append(json.dumps(item, default=str))
            except TypeError:
                serialized_items.append(str(item))
        else:
            serialized_items.append(str(item))
    return "\n".join(serialized_items)


def _summarize_model_response(response: ModelResponse) -> str:
    snippets = []
    for output in response.output:
        text = ItemHelpers.extract_last_content(output)
        if text:
            snippets.append(text)
    return "\n".join(snippets)


class CustomAgentHooks(AgentHooks):
    """Extended hooks that automatically track agent interactions and tool usage."""

    CLEANUP_INTERVAL_SECONDS = 60
    STALE_SESSION_THRESHOLD = timedelta(hours=1)

    def __init__(self) -> None:
        self._sessions: Dict[str, _InteractionSession] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def _cleanup_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self.CLEANUP_INTERVAL_SECONDS)
                await self._remove_stale_sessions()
        except asyncio.CancelledError:
            return

    def _start_cleanup_task(self) -> None:
        if self._cleanup_task and not self._cleanup_task.done():
            return
        try:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        except RuntimeError:
            logger.debug("Could not start cleanup task because no running loop is present yet")

    async def _remove_stale_sessions(self) -> None:
        cutoff = now_user_tz() - self.STALE_SESSION_THRESHOLD
        async with self._lock:
            stale_keys = [key for key, session in self._sessions.items() if session.last_updated < cutoff]
            for key in stale_keys:
                logger.debug("Removing stale interaction session %s", key)
                self._sessions.pop(key, None)

    def _context_payload(self, context: RunContextWrapper) -> InteractionTrackingContext | None:
        payload = getattr(context, "context", None)
        if isinstance(payload, InteractionTrackingContext):
            return payload
        return None

    def _context_id(self, context: RunContextWrapper, agent: Agent, payload: InteractionTrackingContext | None) -> str:
        # Include agent name in the session key to separate sub-agent sessions
        # This ensures efa_agent called as a tool gets its own session
        base_id = payload.context_id if payload and payload.context_id else f"auto-{id(context)}"
        return f"{base_id}::{agent.name}"

    def _create_session(self, context_id: str, agent: Agent, payload: InteractionTrackingContext | None) -> _InteractionSession:
        return _InteractionSession(
            context_id=context_id,
            agent_type=payload.agent_type or agent.name,
            input_data=payload.input_data if payload and payload.input_data else "",
            metadata=dict(payload.metadata) if payload else {},
            system_instructions=agent.instructions,
            start_time=now_user_tz(),
            last_updated=now_user_tz(),
        )

    async def _with_session(
        self,
        context: RunContextWrapper,
        agent: Agent,
        updater: Callable[[_InteractionSession], TUpdateResult],
    ) -> TUpdateResult:
        payload = self._context_payload(context)
        context_id = self._context_id(context, agent, payload)
        async with self._lock:
            session = self._sessions.get(context_id)
            if session is None:
                session = self._create_session(context_id, agent, payload)
                self._sessions[context_id] = session
                self._start_cleanup_task()
            result = updater(session)
            session.last_updated = now_user_tz()
        return result  # type: ignore[return-value]

    async def _pop_session(self, context: RunContextWrapper, agent: Agent) -> _InteractionSession | None:
        payload = self._context_payload(context)
        context_id = self._context_id(context, agent, payload)
        async with self._lock:
            return self._sessions.pop(context_id, None)

    def _commit_session(self, session: _InteractionSession, agent: Agent, output: Any) -> None:
        if session.completed:
            return
        session.completed = True
        tool_records = [call.to_dict() for call in session.tool_calls]
        run_duration = (now_user_tz() - session.start_time).total_seconds()
        metadata = dict(session.metadata)
        metadata.setdefault("tracking_context_id", session.context_id)
        metadata.setdefault("run_duration_seconds", run_duration)
        metadata.setdefault("tool_usage", tool_records if tool_records else None)

        interaction_tracker.track_interaction(
            agent_type=session.agent_type,
            input_data=session.input_data,
            output_data=_serialize_output(output),
            metadata=metadata,
            system_instructions=session.system_instructions,
            tool_usage=tool_records or None,
        )

    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        logger.info("Agent '%s' starting", agent.name)
        await self._with_session(context, agent, lambda session: None)

    async def on_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        logger.info("Agent '%s' finished", agent.name)
        session = await self._pop_session(context, agent)
        if session:
            self._commit_session(session, agent, output)

    async def on_handoff(self, context: RunContextWrapper, agent: Agent, source: Agent) -> None:
        logger.debug("Handoff to agent '%s' from '%s'", agent.name, source.name)

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        logger.info("Agent '%s' starting tool: %s", agent.name, tool.name)
        
        tool_input = None
        if hasattr(context, 'tool_arguments') and context.tool_arguments:
            tool_input = _serialize_output(context.tool_arguments)

        def updater(session: _InteractionSession) -> None:
            session.tool_calls.append(_ToolUsageRecord(tool_name=tool.name, start_time=now_user_tz(), input=tool_input))

        await self._with_session(context, agent, updater)

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str) -> None:
        logger.info("Agent '%s' finished tool '%s'", agent.name, tool.name)

        def updater(session: _InteractionSession) -> None:
            for call in reversed(session.tool_calls):
                if call.tool_name == tool.name and call.end_time is None:
                    call.end_time = now_user_tz()
                    call.result = result
                    break

        await self._with_session(context, agent, updater)

    async def on_llm_start(
        self,
        context: RunContextWrapper,
        agent: Agent,
        system_prompt: Optional[str],
        input_items: list[TResponseInputItem],
    ) -> None:
        logger.debug("Agent '%s' starting LLM call with %d input items", agent.name, len(input_items))

    async def on_llm_end(self, context: RunContextWrapper, agent: Agent, response: ModelResponse) -> None:
        logger.debug("Agent '%s' received LLM response with %d output elements", agent.name, len(response.output))


class LoggingOnlyAgentHooks(AgentHooks):
    """Agent hooks that only log agent activity without tracking interactions."""

    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        logger.info("Agent '%s' starting", agent.name)

    async def on_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        logger.info("Agent '%s' finished", agent.name)

    async def on_handoff(self, context: RunContextWrapper, agent: Agent, source: Agent) -> None:
        logger.debug("Handoff to agent '%s' from '%s'", agent.name, source.name)

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        logger.info("Agent '%s' starting tool: %s", agent.name, tool.name)

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str) -> None:
        logger.info("Agent '%s' finished tool '%s'", agent.name, tool.name)

    async def on_llm_start(
        self,
        context: RunContextWrapper,
        agent: Agent,
        system_prompt: Optional[str],
        input_items: list[TResponseInputItem],
    ) -> None:
        logger.debug("Agent '%s' starting LLM call with %d input items", agent.name, len(input_items))

    async def on_llm_end(self, context: RunContextWrapper, agent: Agent, response: ModelResponse) -> None:
        logger.debug("Agent '%s' received LLM response with %d output elements", agent.name, len(response.output))


__all__ = ["CustomAgentHooks", "LoggingOnlyAgentHooks", "InteractionTrackingContext"]
