import asyncio
import os
from contextlib import asynccontextmanager

import uvicorn
from agents import set_default_openai_client, set_tracing_disabled
from litestar import Litestar, get
from litestar.static_files import create_static_files_router
from openai import AsyncOpenAI

AI_ENDPOINT_URL = os.getenv("AI_ENDPOINT_URL", None)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

kwargs = dict(api_key=OPENAI_API_KEY)

if AI_ENDPOINT_URL:
    kwargs["base_url"] = AI_ENDPOINT_URL

custom_client = AsyncOpenAI(**kwargs)
set_default_openai_client(custom_client)
set_tracing_disabled(True)

from aiagents.ai_scheduler import determine_next_run_by_memory
from controllers.api_controller import APIController
from services.matrix_bot import matrix_chat_bot
from services.ai_scheduler import ai_scheduler
from services.migration import migrate_json_to_mongodb


@asynccontextmanager
async def lifespan(app: Litestar):
    """Manage the lifespan of the Litestar app and Matrix bot"""
    # Run migration on startup
    migrate_json_to_mongodb()
    
    asyncio.create_task(matrix_chat_bot.start())
    ai_scheduler.start()
    asyncio.create_task(determine_next_run_by_memory())
    print("Services started")

    yield

    await matrix_chat_bot.stop()
    ai_scheduler.stop()
    print("Services stopped")


@get("/health")
async def health_check() -> dict:
    """Health check endpoint for Docker"""
    return {"status": "healthy"}


# Create static files router for the Vue.js frontend
static_files_router = create_static_files_router(
    path="/",
    directories=["ui/dist"],
    html_mode=True,
    name="static"
)

app = Litestar(
    route_handlers=[APIController, health_check, static_files_router],
    lifespan=[lifespan],
)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8200)
