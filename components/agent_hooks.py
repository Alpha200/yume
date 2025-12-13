import logging
from typing import Optional

from agents import Agent
from agents.lifecycle import AgentHooks
from agents.run_context import RunContextWrapper
from agents.tool import Tool
from agents.items import ModelResponse, TResponseInputItem

logger = logging.getLogger(__name__)


class CustomAgentHooks(AgentHooks):
    """Custom agent hooks that log lifecycle events."""

    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        """Called before the agent is invoked."""
        logger.debug(f"Agent '{agent.name}' starting")

    async def on_end(self, context: RunContextWrapper, agent: Agent, output) -> None:
        """Called when the agent produces a final output."""
        logger.debug(f"Agent '{agent.name}' finished with output: {str(output)[:100]}...")

    async def on_handoff(self, context: RunContextWrapper, agent: Agent, source: Agent) -> None:
        """Called when the agent is being handed off to."""
        logger.debug(f"Handoff to agent '{agent.name}' from '{source.name}'")

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        """Called concurrently with tool invocation."""
        logger.debug(f"Agent '{agent.name}' starting tool: {tool.name}")

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str) -> None:
        """Called after a tool is invoked."""
        logger.debug(f"Agent '{agent.name}' finished tool '{tool.name}' with result length: {len(result)}")

    async def on_llm_start(self, context: RunContextWrapper, agent: Agent, system_prompt: Optional[str], input_items: list[TResponseInputItem]) -> None:
        """Called immediately before the agent issues an LLM call."""
        logger.debug(f"Agent '{agent.name}' starting LLM call with {len(input_items)} input items")

    async def on_llm_end(self, context: RunContextWrapper, agent: Agent, response: ModelResponse) -> None:
        """Called immediately after the agent receives the LLM response."""
        logger.debug(f"Agent '{agent.name}' received LLM response with {len(response.output)} output elements")
