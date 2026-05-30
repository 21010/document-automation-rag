from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.api.health_router import router as health_router
from src.api.routes import router
from src.core.config import settings
from src.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    await init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME, description="RAG-based Invoice Processing API", version="1.0.0", lifespan=lifespan
)

app.include_router(health_router)
app.include_router(router)


def main():
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=False)  # nosec B104


if __name__ == "__main__":
    main()
