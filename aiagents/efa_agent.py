"""
EFA (Elektronisches Fahrplanauskun ftssystem) Agent
Handles public transport queries and provides departure information for stations.
"""

import os
from agents import Agent, Runner, RunConfig, ModelSettings
from pydantic import BaseModel

from components.agent_hooks import CustomAgentHooks
from components.logging_manager import logging_manager
from tools.efa import get_station_departures

logger = logging_manager

USER_LANGUAGE = os.getenv("USER_LANGUAGE", "en")
AI_MODEL = os.getenv("AI_ASSISTANT_MODEL", "gpt-4o-mini")


class DepartureQueryResult(BaseModel):
    """Result of an EFA departure query"""
    departure_info: str
    reasoning: str


# Initialize the EFA agent with tools
efa_agent = Agent(
    id="efa_agent",
    model_settings=ModelSettings(
        model_name=AI_MODEL,
    ),
    instructions=f"""
You are an EFA (Elektronisches Fahrplanauskun ftssystem) tool. Your role is to fetch and provide public transport departure information.

You will receive queries about public transport departures and should:
1. Extract the station name
2. Extract any filters: line numbers (e.g., "U47", "RB12") or destinations (e.g., "Berlin", "Köln")
3. Call the appropriate tool to fetch departure information
4. Return the results exactly as provided by the tool

Rules:
- Extract information from the query accurately
- When users ask about departures to specific destinations, use the direction filter
- When users ask about specific lines or line numbers, use the line filter
- Combine filters when both are present in the query
- Return the departure information as-is without additional commentary
- Do not add interpretation or personal observations

Tool available:
- get_station_departures: Fetch departures with optional line and direction filters
    """.strip(),
    hooks=CustomAgentHooks(),
    tools=[
        get_station_departures,
    ],
    output_type=DepartureQueryResult,
)


async def query_departures(query: str) -> DepartureQueryResult:
    """
    Query EFA for departure information based on natural language input.
    
    Args:
        query: Natural language question about departures (e.g., "What trains go from Essen to Berlin?")
    
    Returns:
        DepartureQueryResult with departure info and reasoning
    """
    try:
        logger.log(f"[EFA_AGENT] Processing departure query: {query[:80]}...")
        
        result = await Runner.run(efa_agent, query, run_config=RunConfig(tracing_disabled=True))
        
        # Try to parse as DepartureQueryResult if possible
        try:
            departure_result = result.final_output_as(DepartureQueryResult)
            return departure_result
        except:
            # Fall back to raw final message
            departure_info = result.final_message or str(result.output)
            return DepartureQueryResult(
                departure_info=departure_info,
                reasoning="Query processed successfully"
            )
        
    except Exception as e:
        logger.log(f"[EFA_AGENT] Error processing query: {e}")
        return DepartureQueryResult(
            departure_info=f"Error processing your query: {str(e)}",
            reasoning=f"Exception: {type(e).__name__}"
        )
