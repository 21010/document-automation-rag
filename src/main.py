import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.health_router import router as health_router
from src.api.routes import router
from src.core.config import settings
from src.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    await init_db()
    yield


logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME, description="RAG-based Invoice Processing API", version="1.0.0", lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Telemetry Middleware
@app.middleware("http")
async def add_telemetry_logging(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    logger.info(
        f"Telemetry: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s"
    )
    return response


app.include_router(health_router)
app.include_router(router)


def main():
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=False)  # nosec B104


if __name__ == "__main__":
    main()
