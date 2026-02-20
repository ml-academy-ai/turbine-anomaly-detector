FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# Some Python packages (like `catboost`, `torch`) require compilation tools.
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Copy entire project (needed for uv sync to read version from __init__.py)
COPY . .

# Install Python dependencies using uv
# uv sync creates a virtual environment and installs only main dependencies (no dev/eda extras)
# --frozen: will fail if the lockfile and pyproject.toml disagree 
# (e.g. a new dependency in pyproject.toml not in the lockfile)
RUN uv sync --frozen

# Set Python path and ensure venv is in PATH
# Adds /app/src to PYTHONPATH, so Python can import your turbine_anomaly_detector package.
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Adds the virtual environment’s bin directory to PATH.
# Python, pip, kedro, uv, etc. from .venv can be run directly, 
# so you don’t need to use uv run or full paths.
ENV PATH="/app/.venv/bin:$PATH"

# Default command (can be overridden in docker-compose)
CMD ["python", "--version"]