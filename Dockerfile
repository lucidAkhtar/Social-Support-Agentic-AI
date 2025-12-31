# Production Dockerfile for Social Support Agentic AI System
# Multi-stage build for optimized image size

FROM python:3.10-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry==1.7.1

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (production only)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# ===== Production stage =====
FROM python:3.10-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code (excluding unnecessary files via .dockerignore)
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser models/ ./models/
COPY --chown=appuser:appuser data/ ./data/
COPY --chown=appuser:appuser streamlit_app/ ./streamlit_app/
COPY --chown=appuser:appuser pyproject.toml ./

# Create necessary directories with proper permissions
RUN mkdir -p data/databases data/processed data/raw data/observability logs \
    && chown -R appuser:appuser data logs models

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check - verify core API is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI application
# 6 Agents: Extraction, Validation, Eligibility, Recommendation, Explanation, RAG Chatbot
# 4 Databases: SQLite, TinyDB, ChromaDB, NetworkX Graph
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
