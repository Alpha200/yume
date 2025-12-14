"""Service to track agent interactions for debugging purposes"""
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from components.timezone_utils import now_user_tz


@dataclass
class AgentInteraction:
    """Represents a single agent interaction with full input and output"""
    id: str
    agent_type: str  # e.g., "ai_engine", "memory_manager", "ai_scheduler"
    timestamp: datetime
    input_data: str
    output_data: str
    metadata: Optional[Dict[str, Any]] = None
    system_instructions: Optional[str] = None
    tool_usage: Optional[List[Dict[str, Any]]] = None
    llm_calls: Optional[List[Dict[str, Any]]] = None


class InteractionTracker:
    """Tracks agent interactions for debugging in the web UI"""

    def __init__(self, max_interactions: int = 20):
        self.max_interactions = max_interactions
        self.interactions: deque[AgentInteraction] = deque(maxlen=max_interactions)
        self._counter = 0

    def track_interaction(
        self,
        agent_type: str,
        input_data: str,
        output_data: str,
        metadata: Optional[Dict[str, Any]] = None,
        system_instructions: Optional[str] = None,
        tool_usage: Optional[List[Dict[str, Any]]] = None,
        llm_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Track a new agent interaction

        Args:
            agent_type: Type of agent (e.g., "ai_engine", "memory_manager")
            input_data: Full input sent to the agent
            output_data: Full output received from the agent
            metadata: Optional metadata about the interaction
            system_instructions: Optional system instructions/prompt used for the interaction

        Returns:
            The ID of the tracked interaction
        """
        self._counter += 1
        interaction_id = f"interaction_{self._counter}"

        interaction = AgentInteraction(
            id=interaction_id,
            agent_type=agent_type,
            timestamp=now_user_tz(),
            input_data=input_data,
            output_data=output_data,
            metadata=metadata or {},
            system_instructions=system_instructions,
            tool_usage=tool_usage,
            llm_calls=llm_calls,
        )

        self.interactions.append(interaction)
        return interaction_id

    def get_all_interactions(self) -> List[AgentInteraction]:
        """Get all tracked interactions, newest first"""
        return list(reversed(self.interactions))

    def get_interaction_by_id(self, interaction_id: str) -> Optional[AgentInteraction]:
        """Get a specific interaction by ID"""
        for interaction in self.interactions:
            if interaction.id == interaction_id:
                return interaction
        return None

    def clear_interactions(self):
        """Clear all tracked interactions"""
        self.interactions.clear()


# Global interaction tracker instance
interaction_tracker = InteractionTracker(max_interactions=20)

