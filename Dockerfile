# Stage 1: Build
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies needed during build
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy only dependency files to leverage caching
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.13-slim

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY src/ /app/src/

# Create directory for uploads and ensure permissions
RUN mkdir -p /app/data/uploads

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Command to run the application
CMD ["python", "-m", "src.main"]
