import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from services.ai_scheduler import AIScheduler
from services.matrix_bot import MatrixChatBot


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Manage the lifespan of the FastAPI app and Matrix bot"""
    matrix_bot = MatrixChatBot()
    ai_scheduler = AIScheduler()

    asyncio.create_task(matrix_bot.start())
    ai_scheduler.start()
    print("Services started")

    yield

    await matrix_bot.stop()
    ai_scheduler.stop()
    print("Services stopped")


app = FastAPI(title="Yume", version="0.1.0", lifespan=lifespan)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8200)
