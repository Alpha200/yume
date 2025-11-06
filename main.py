import asyncio
import os
from contextlib import asynccontextmanager

import uvicorn
from agents import set_default_openai_client, set_tracing_disabled
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
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
from controllers.api_controller import router as api_router
from services.matrix_bot import matrix_chat_bot
from services.ai_scheduler import ai_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Manage the lifespan of the FastAPI app and Matrix bot"""
    asyncio.create_task(matrix_chat_bot.start())
    ai_scheduler.start()
    asyncio.create_task(determine_next_run_by_memory())
    print("Services started")

    yield

    await matrix_chat_bot.stop()
    ai_scheduler.stop()
    print("Services stopped")


app = FastAPI(title="Yume", version="0.1.0", lifespan=lifespan)

# Include API routes
app.include_router(api_router)

# Health check endpoint for Docker
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Mount static files for the built Vue.js frontend
app.mount("/", StaticFiles(directory="ui/dist", html=True), name="static")

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8200)
