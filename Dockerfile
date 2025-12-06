# Multi-stage build for Vue.js frontend and Python backend

# Stage 1: Build Vue.js frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/ui

# Copy package files
COPY ui/package*.json ./
RUN npm ci

# Copy source code and build
COPY ui/ ./
RUN npm run build

# Stage 2: Python backend with built frontend
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (minimal for MongoDB)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure poetry: Don't create virtual environment (we're in a container)
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --only main --no-interaction --no-ansi

# Copy application code
COPY . .

# Copy built frontend from the first stage
COPY --from=frontend-builder /app/ui/dist ./ui/dist

# Expose port
EXPOSE 8200

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8200/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8200"]
