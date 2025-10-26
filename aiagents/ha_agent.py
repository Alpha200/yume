import os
from contextlib import asynccontextmanager

from agents import Agent
from agents.mcp import MCPServerSse
from pydantic import BaseModel

from components.agent_hooks import CustomAgentHooks

HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN")

INSTRUCTIONS = """
You are responsible for managing and controlling smart home devices via Home Assistant

Through the Home Assistant tools, you have access to:
1. Device states and sensor data (lights, switches, sensors, etc.)
2. Service calls to control devices and automation

DEVICE CONTROL:
- Always check current device states before making changes
- Explain what you're doing and why when controlling devices
- Execute the requested actions

Guidelines:
- Never disable critical security or safety systems

Output the result of your action taken and a brief reasoning summary
"""

class HomeAssistantResult(BaseModel):
    reasoning_summary: str
    result: str

mcp_server_home_assistant = MCPServerSse(
    name="home-assistant",
    params=dict(
        url=HA_URL + "/mcp_server/sse",
        headers=dict(
            Authorization=f"Bearer {HA_TOKEN}"
        )
    ),
)


@asynccontextmanager
def get_home_assistant_agent():
    with mcp_server_home_assistant as mcp_home_assistant:
        home_assistant_agent = Agent(
            name='Home Assistant',
            model="gpt-4o-mini",
            instructions=INSTRUCTIONS,
            hooks=CustomAgentHooks(),
            output_type=HomeAssistantResult,
            mcp_servers = [mcp_home_assistant],
        )

        yield home_assistant_agent