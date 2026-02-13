# Session 17: Deep-Dive into Docker and Docker Compose

## Overview

This session covers containerizing your ML application using Docker and Docker Compose. You'll learn how to:

- Create a Dockerfile for your application
- Set up Docker Compose for local development
- Configure Docker Compose for production/CD pipeline deployment
- Run MLflow, Kedro Viz, training, inference, and UI services in containers
- Manage volumes, networks, and service dependencies

## Prerequisites

- Docker Desktop installed and running
- Basic understanding of Docker concepts (containers, images, volumes)
- Your ML application is working locally

## Part 1: Understanding the Docker Setup

### Architecture Overview

Our Docker setup consists of 6 services:

1. **mlflow**: MLflow tracking server for experiment tracking and model registry
2. **app-ml-train**: Trains the ML model (runs once, then stops)
3. **app-ml-inference**: Runs inference on new data (monitors for new data continuously)
4. **app-stream-data**: Streams data to database for real-time inference
5. **app-ui**: Web dashboard for visualizing predictions and model metrics
6. **kedro-viz**: Pipeline visualization tool

### Key Concepts

- **Volumes**: Shared folders between host and containers (persist data)
- **Ports**: Expose container ports to host machine (access services)
- **Networks**: Allow services to communicate using service names
- **Depends_on**: Service startup order dependencies

## Part 2: Creating the Dockerfile

### Step 1: Understand the Base Image

Our Dockerfile uses `python:3.12-slim` as the base image:
- Lightweight Debian-based image
- Python 3.12 pre-installed
- Suitable for production deployments

### Step 2: Install System Dependencies

```dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*
```

**Why?** Some Python packages (like `catboost`, `torch`) require compilation tools.

### Step 3: Install uv Package Manager

```dockerfile
RUN pip install --no-cache-dir uv
```

**Why uv?** 
- Faster than pip for dependency resolution
- Better lock file support
- Handles virtual environments automatically

### Step 4: Copy Dependency Files

```dockerfile
COPY pyproject.toml uv.lock ./
```

**Why both?**
- `pyproject.toml`: Project metadata and dependencies
- `uv.lock`: Locked versions for reproducible builds

### Step 5: Copy Entire Project

```dockerfile
COPY . .
```

**Important:** This must be done BEFORE `uv sync` because:
- `pyproject.toml` uses `dynamic = ["version"]`
- Version is read from `src/ml_app_wind_draft/__init__.py`
- Source code must be present for version detection

### Step 6: Install Python Dependencies

```dockerfile
RUN uv sync --frozen
```

**Flags explained:**
- `--frozen`: Use exact versions from `uv.lock` (reproducible)

### Step 7: Set Environment Variables

```dockerfile
ENV PYTHONPATH=/app/src:$PYTHONPATH
ENV PATH="/app/.venv/bin:$PATH"
```

**Why?**
- `PYTHONPATH`: Allows imports from `src/` directory
- `PATH`: Makes `python`, `kedro`, etc. available in PATH

### Complete Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
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
RUN uv sync --frozen

# Set Python path and ensure venv is in PATH
ENV PYTHONPATH=/app/src:$PYTHONPATH
ENV PATH="/app/.venv/bin:$PATH"

# Default command (can be overridden in docker-compose)
CMD ["python", "--version"]
```

## Part 3: Introduction to Docker Registry and Manual Pushing

### Step 1: Understanding Docker Registry

A **Docker registry** is a storage and distribution system for Docker images. It allows you to:
- Store Docker images in a centralized location
- Share images across different machines and environments
- Version control your application images
- Enable automated deployments

**Common Docker registries:**
- **Docker Hub**: Public registry (default, free tier available)
- **GitHub Container Registry (ghcr.io)**: Integrated with GitHub
- **Amazon ECR**: AWS container registry
- **Google Container Registry**: GCP container registry
- **Azure Container Registry**: Microsoft Azure registry
- **Private registries**: Self-hosted solutions

**For this session, we'll use Docker Hub** as it's the most common and free to use.

### Step 2: Create Docker Hub Account

1. **Sign up for Docker Hub:**
   - Go to https://hub.docker.com
   - Click "Sign Up" and create an account
   - Verify your email address

2. **Create a repository:**
   - Click "Create Repository"
   - Repository name: `ml-app-wind-draft` (or your preferred name)
   - Visibility: Public (free) or Private (requires paid plan)
   - Click "Create"

3. **Note your repository path:**
   - Format: `YOUR_USERNAME/ml-app-wind-draft`
   - Example: `johndoe/ml-app-wind-draft`

### Step 3: Build Docker Image Locally

1. **Navigate to project directory:**
   ```bash
   cd /path/to/ml-app-wind-draft
   ```

2. **Build the Docker image:**
   ```bash
   docker build -t YOUR_USERNAME/ml-app-wind-draft:latest .
   ```

   **Command breakdown:**
   - `docker build`: Build command
   - `-t YOUR_USERNAME/ml-app-wind-draft:latest`: Tag the image
     - `YOUR_USERNAME/ml-app-wind-draft`: Repository name
     - `:latest`: Tag (version identifier)
   - `.`: Build context (current directory)

3. **Verify image was created:**
   ```bash
   docker images
   # Should see: YOUR_USERNAME/ml-app-wind-draft:latest
   ```

### Step 4: Tag Docker Image

Tags allow you to version your images. You can create multiple tags:

1. **Tag with version number:**
   ```bash
   docker tag YOUR_USERNAME/ml-app-wind-draft:latest YOUR_USERNAME/ml-app-wind-draft:v1.0.0
   ```

2. **Tag with commit hash:**
   ```bash
   docker tag YOUR_USERNAME/ml-app-wind-draft:latest YOUR_USERNAME/ml-app-wind-draft:$(git rev-parse --short HEAD)
   ```

3. **Verify tags:**
   ```bash
   docker images YOUR_USERNAME/ml-app-wind-draft
   # Should show multiple tags pointing to same image
   ```

**Why multiple tags?**
- `latest`: Always points to most recent version
- Version tags (`v1.0.0`): Specific versions for rollback
- Commit tags: Track which code version is in image

### Step 5: Log in to Docker Hub

1. **Log in from command line:**
   ```bash
   docker login
   ```

2. **Enter credentials:**
   - Username: Your Docker Hub username
   - Password: Your Docker Hub password (or access token)

3. **Verify login:**
   ```bash
   docker info | grep Username
   # Should show your username
   ```

**Alternative: Using access token (recommended for CI/CD):**

1. **Create access token:**
   - Go to Docker Hub → Account Settings → Security
   - Click "New Access Token"
   - Name: `github-actions` (or descriptive name)
   - Permissions: Read & Write
   - Copy the token (shown only once)

2. **Log in with token:**
   ```bash
   echo "YOUR_ACCESS_TOKEN" | docker login --username YOUR_USERNAME --password-stdin
   ```

### Step 6: Push Image to Docker Hub

1. **Push latest tag:**
   ```bash
   docker push YOUR_USERNAME/ml-app-wind-draft:latest
   ```

2. **Push version tag:**
   ```bash
   docker push YOUR_USERNAME/ml-app-wind-draft:v1.0.0
   ```

3. **Push all tags:**
   ```bash
   docker push YOUR_USERNAME/ml-app-wind-draft --all-tags
   ```

**What happens:**
- Docker uploads image layers to Docker Hub
- Progress is shown for each layer
- Image becomes available in your repository

### Step 7: Verify Image on Docker Hub

1. **Check repository:**
   - Go to https://hub.docker.com/r/YOUR_USERNAME/ml-app-wind-draft
   - You should see your pushed image with tags

2. **Test pulling image:**
   ```bash
   # Remove local image
   docker rmi YOUR_USERNAME/ml-app-wind-draft:latest

   # Pull from Docker Hub
   docker pull YOUR_USERNAME/ml-app-wind-draft:latest

   # Verify
   docker images YOUR_USERNAME/ml-app-wind-draft
   ```

### Step 8: Complete Manual Push Workflow

Here's the complete workflow for building and pushing:

```bash
# 1. Build image
docker build -t YOUR_USERNAME/ml-app-wind-draft:latest .

# 2. Tag with version (optional)
docker tag YOUR_USERNAME/ml-app-wind-draft:latest YOUR_USERNAME/ml-app-wind-draft:v1.0.0

# 3. Log in to Docker Hub
docker login

# 4. Push image
docker push YOUR_USERNAME/ml-app-wind-draft:latest
docker push YOUR_USERNAME/ml-app-wind-draft:v1.0.0

# 5. Verify on Docker Hub
# Visit: https://hub.docker.com/r/YOUR_USERNAME/ml-app-wind-draft
```

### Step 9: Using Pushed Images

Once your image is on Docker Hub, you can use it anywhere:

1. **Pull and run locally:**
   ```bash
   docker pull YOUR_USERNAME/ml-app-wind-draft:latest
   docker run YOUR_USERNAME/ml-app-wind-draft:latest
   ```

2. **Use in docker-compose.yml:**
   ```yaml
   services:
     app-ui:
       image: YOUR_USERNAME/ml-app-wind-draft:latest
       # ... rest of configuration
   ```

3. **Use on remote server:**
   ```bash
   # On DigitalOcean droplet or any server
   docker pull YOUR_USERNAME/ml-app-wind-draft:latest
   docker compose up -d
   ```

### Step 10: Image Naming Best Practices

**Good naming conventions:**
- `username/repository:tag`
- Use semantic versioning: `v1.0.0`, `v1.0.1`, `v2.0.0`
- Use `latest` for most recent stable version
- Use descriptive tags: `dev`, `staging`, `production`

**Examples:**
```bash
# Version tags
docker tag ml-app-wind-draft:latest johndoe/ml-app-wind-draft:v1.0.0
docker tag ml-app-wind-draft:latest johndoe/ml-app-wind-draft:v1.0.1

# Environment tags
docker tag ml-app-wind-draft:latest johndoe/ml-app-wind-draft:dev
docker tag ml-app-wind-draft:latest johndoe/ml-app-wind-draft:staging
docker tag ml-app-wind-draft:latest johndoe/ml-app-wind-draft:production

# Commit-based tags
docker tag ml-app-wind-draft:latest johndoe/ml-app-wind-draft:abc1234
```

### Step 11: Managing Images

1. **List local images:**
   ```bash
   docker images
   docker images YOUR_USERNAME/ml-app-wind-draft
   ```

2. **Remove local image:**
   ```bash
   docker rmi YOUR_USERNAME/ml-app-wind-draft:latest
   ```

3. **Remove all tags of an image:**
   ```bash
   docker rmi $(docker images YOUR_USERNAME/ml-app-wind-draft -q)
   ```

4. **Clean up unused images:**
   ```bash
   docker image prune
   docker image prune -a  # Remove all unused images
   ```

### Step 12: Troubleshooting Push Issues

**Issue 1: Authentication failed**

**Error:** `denied: requested access to the resource is denied`

**Solutions:**
- Verify username and password are correct
- Check if repository name matches Docker Hub repository
- Ensure you have write access to the repository
- Try logging out and back in: `docker logout` then `docker login`

**Issue 2: Image not found**

**Error:** `repository name must be lowercase`

**Solution:**
- Docker Hub requires lowercase repository names
- Use: `johndoe/ml-app-wind-draft` not `JohnDoe/ML-App-Wind-Draft`

**Issue 3: Push timeout**

**Error:** `context deadline exceeded`

**Solutions:**
- Check internet connection
- Try pushing during off-peak hours
- Use Docker Hub mirror if available
- Consider using a different registry (e.g., GitHub Container Registry)

**Issue 4: Layer already exists**

**Message:** `Layer already exists`

**This is normal:** Docker skips uploading layers that already exist in the registry, making subsequent pushes faster.

## Part 4: Building Docker Compose for Local Development

### Step 1: Understanding Local Development Setup

For local development, we use `docker-compose.local.yml` which:
- Builds images from source code
- Mounts source code as volumes (optional, for live code changes)
- Uses default environment variables
- Perfect for development and testing

### Step 2: Create MLflow Service

```yaml
mlflow:
  build:
    context: .                    # Build context is the project root
    dockerfile: Dockerfile        # Use the shared Dockerfile
  command: >
    sh -c "mlflow server 
    --host 0.0.0.0 
    --port 5001 
    --default-artifact-root file:///app/mlflow/mlartifacts
    --allowed-hosts '*'
    --cors-allowed-origins '*'"
  ports:
    - "5001:5001"                 # Expose port 5001 for MLflow UI
  volumes:
    - ./mlflow:/app/mlflow       # MLflow runs and artifacts
    - ./data:/app/data           # Access to data
    - ./conf:/app/conf           # Configuration files
  networks:
    - ml-app-network
  restart: unless-stopped
```

**Key points:**
- `build`: Builds image from source using Dockerfile
- `command`: Runs MLflow server with file-based storage
- `volumes`: Mounts local directories for persistence
- `--allowed-hosts '*'`: Fixes "Invalid Host header" errors

### Step 3: Create UI Service

```yaml
app-ui:
  build:
    context: .
    dockerfile: Dockerfile
  command: ["python", "entrypoint/app_ui.py"]
  ports:
    - "8050:8050"
  volumes:
    - ./data:/app/data
    - ./conf:/app/conf
    - ./mlflow:/app/mlflow
  environment:
    - KEDRO_ENV=local
    - MLFLOW_TRACKING_URI=http://mlflow:5001
    - MLFLOW_UI_URI=${MLFLOW_UI_URI:-http://localhost:5001}
    - DEBUG=False
    - KEDRO_VIZ_URI=${KEDRO_VIZ_URI:-http://localhost:4141}
  networks:
    - ml-app-network
  restart: unless-stopped
  depends_on:
    - mlflow
```

**Key points:**
- Uses service name `mlflow:5001` for internal communication
- Default values for environment variables (local development)
- Depends on MLflow service

### Step 4: Create Training Service

```yaml
app-ml-train:
  build:
    context: .
    dockerfile: Dockerfile
  command: ["python", "entrypoint/training.py"]
  volumes:
    - ./data:/app/data
    - ./conf:/app/conf
    - ./mlflow:/app/mlflow
  environment:
    - KEDRO_ENV=local
    - MLFLOW_TRACKING_URI=http://mlflow:5001
  networks:
    - ml-app-network
  restart: "no"                   # Only run once
  depends_on:
    - mlflow
    - app-ui
```

**Key points:**
- `restart: "no"`: Runs once, then stops
- Waits for MLflow and UI to be ready

### Step 5: Create Inference Service

```yaml
app-ml-inference:
  build:
    context: .
    dockerfile: Dockerfile
  command: ["python", "entrypoint/inference_real_time.py"]
  volumes:
    - ./data:/app/data
    - ./conf:/app/conf
    - ./mlflow:/app/mlflow
  environment:
    - KEDRO_ENV=local
    - MLFLOW_TRACKING_URI=http://mlflow:5001
  networks:
    - ml-app-network
  restart: unless-stopped
  depends_on:
    app-ml-train:
      condition: service_completed_successfully
```

**Key points:**
- `condition: service_completed_successfully`: Waits for training to finish
- Runs continuously, monitoring for new data

### Step 6: Create Data Streaming Service

```yaml
app-stream-data:
  build:
    context: .
    dockerfile: Dockerfile
  command: ["python", "entrypoint/app_stream_data.py"]
  volumes:
    - ./data:/app/data
    - ./conf:/app/conf
  networks:
    - ml-app-network
  restart: unless-stopped
  depends_on:
    - mlflow
```

**Key points:**
- Streams data point-by-point to simulate real-time ingestion
- Required for inference to have data to process

### Step 7: Create Kedro Viz Service

```yaml
kedro-viz:
  build:
    context: .
    dockerfile: Dockerfile
  command: ["kedro", "viz", "--host", "0.0.0.0", "--port", "4141"]
  ports:
    - "4141:4141"
  networks:
    - ml-app-network
  restart: unless-stopped
  depends_on:
    - app-ml-inference
```

**Key points:**
- Pipeline visualization tool
- Uses `kedro viz` command from the container

### Step 8: Create Network Configuration

```yaml
networks:
  ml-app-network:
    driver: bridge
```

**Why?**
- Bridge network allows services to communicate using service names
- Isolated from other Docker networks

### Complete Local Development Docker Compose

Create `docker-compose.local.yml`:

```yaml
services:
  mlflow:
    build:
      context: .
      dockerfile: Dockerfile
    command: >
      sh -c "mlflow server 
      --host 0.0.0.0 
      --port 5001 
      --default-artifact-root file:///app/mlflow/mlartifacts
      --allowed-hosts '*'
      --cors-allowed-origins '*'"
    ports:
      - "5001:5001"
    volumes:
      - ./mlflow:/app/mlflow
      - ./data:/app/data
      - ./conf:/app/conf
    networks:
      - ml-app-network
    restart: unless-stopped

  app-ui:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["python", "entrypoint/app_ui.py"]
    ports:
      - "8050:8050"
    volumes:
      - ./data:/app/data
      - ./conf:/app/conf
      - ./mlflow:/app/mlflow
    environment:
      - KEDRO_ENV=local
      - MLFLOW_TRACKING_URI=http://mlflow:5001
      - MLFLOW_UI_URI=${MLFLOW_UI_URI:-http://localhost:5001}
      - DEBUG=False
      - KEDRO_VIZ_URI=${KEDRO_VIZ_URI:-http://localhost:4141}
    networks:
      - ml-app-network
    restart: unless-stopped
    depends_on:
      - mlflow

  app-ml-train:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["python", "entrypoint/training.py"]
    volumes:
      - ./data:/app/data
      - ./conf:/app/conf
      - ./mlflow:/app/mlflow
    environment:
      - KEDRO_ENV=local
      - MLFLOW_TRACKING_URI=http://mlflow:5001
    networks:
      - ml-app-network
    restart: "no"
    depends_on:
      - mlflow
      - app-ui

  app-ml-inference:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["python", "entrypoint/inference_real_time.py"]
    volumes:
      - ./data:/app/data
      - ./conf:/app/conf
      - ./mlflow:/app/mlflow
    environment:
      - KEDRO_ENV=local
      - MLFLOW_TRACKING_URI=http://mlflow:5001
    networks:
      - ml-app-network
    restart: unless-stopped
    depends_on:
      app-ml-train:
        condition: service_completed_successfully

  app-stream-data:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["python", "entrypoint/app_stream_data.py"]
    volumes:
      - ./data:/app/data
      - ./conf:/app/conf
    networks:
      - ml-app-network
    restart: unless-stopped
    depends_on:
      - mlflow

  kedro-viz:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["kedro", "viz", "--host", "0.0.0.0", "--port", "4141"]
    ports:
      - "4141:4141"
    networks:
      - ml-app-network
    restart: unless-stopped
    depends_on:
      - app-ml-inference

networks:
  ml-app-network:
    driver: bridge
```

### Step 9: Running Local Development Setup

```bash
# Build and start all services
docker compose -f docker-compose.local.yml up --build

# Start in background
docker compose -f docker-compose.local.yml up --build -d

# Start specific services
docker compose -f docker-compose.local.yml up mlflow app-ui

# View logs
docker compose -f docker-compose.local.yml logs -f

# Stop services
docker compose -f docker-compose.local.yml down
```

**Access services:**
- MLflow UI: http://localhost:5001
- App UI: http://localhost:8050
- Kedro Viz: http://localhost:4141

## Part 5: Building Docker Compose for CD Pipeline

### Step 1: Understanding Production/CD Setup

For production and CD pipeline deployment, we use `docker-compose.yml` which:
- Pulls pre-built images from Docker Hub
- Requires environment variables to be set
- No source code mounting (code is in the image)
- Optimized for production deployments

### Step 2: Environment Variables Setup

**Required environment variables:**

1. **`DOCKERHUB_USERNAME`**: Your Docker Hub username for pulling images
2. **`MLFLOW_UI_URI`**: External URL for MLflow UI (e.g., `http://your-server-ip:5001`)
3. **`KEDRO_VIZ_URI`**: External URL for Kedro Viz (e.g., `http://your-server-ip:4141`)
4. **`MLFLOW_TRACKING_URI`**: MLflow tracking URI (defaults to `http://mlflow:5001`)

**Method 1: Create `.env` file (Recommended)**

Create `.env` in project root:

```bash
DOCKERHUB_USERNAME=your-dockerhub-username
MLFLOW_UI_URI=http://your-server-ip:5001
KEDRO_VIZ_URI=http://your-server-ip:4141
MLFLOW_TRACKING_URI=http://mlflow:5001
```

**Method 2: Export in Shell**

```bash
export DOCKERHUB_USERNAME=your-dockerhub-username
export MLFLOW_UI_URI=http://your-server-ip:5001
export KEDRO_VIZ_URI=http://your-server-ip:4141
export MLFLOW_TRACKING_URI=http://mlflow:5001
```

### Step 3: Create Production Services

The main difference from local development is using `image` instead of `build`:

```yaml
services:
  mlflow:
    image: ${DOCKERHUB_USERNAME}/ml-app-wind-draft:latest
    command: >
      sh -c "mlflow server 
      --host 0.0.0.0 
      --port 5001 
      --default-artifact-root file:///app/mlflow/mlartifacts
      --allowed-hosts '*'
      --cors-allowed-origins '*'"
    ports:
      - "5001:5001"
    volumes:
      - ./mlflow:/app/mlflow
      - ./data:/app/data
      - ./conf:/app/conf
    networks:
      - ml-app-network
    restart: unless-stopped

  app-ui:
    image: ${DOCKERHUB_USERNAME}/ml-app-wind-draft:latest
    command: ["python", "entrypoint/app_ui.py"]
    ports:
      - "8050:8050"
    volumes:
      - ./data:/app/data
      - ./conf:/app/conf
      - ./mlflow:/app/mlflow
    environment:
      - KEDRO_ENV=local
      - MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI:-http://mlflow:5001}
      - MLFLOW_UI_URI=${MLFLOW_UI_URI}
      - DEBUG=False
      - KEDRO_VIZ_URI=${KEDRO_VIZ_URI}
    networks:
      - ml-app-network
    restart: unless-stopped
    depends_on:
      - mlflow

  app-ml-train:
    image: ${DOCKERHUB_USERNAME}/ml-app-wind-draft:latest
    command: ["python", "entrypoint/training.py"]
    volumes:
      - ./data:/app/data
      - ./conf:/app/conf
      - ./mlflow:/app/mlflow
    environment:
      - KEDRO_ENV=local
      - MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI:-http://mlflow:5001}
    networks:
      - ml-app-network
    restart: "no"
    depends_on:
      - mlflow
      - app-ui

  app-ml-inference:
    image: ${DOCKERHUB_USERNAME}/ml-app-wind-draft:latest
    command: ["python", "entrypoint/inference_real_time.py"]
    volumes:
      - ./data:/app/data
      - ./conf:/app/conf
      - ./mlflow:/app/mlflow
    environment:
      - KEDRO_ENV=local
      - MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI:-http://mlflow:5001}
    networks:
      - ml-app-network
    restart: unless-stopped
    depends_on:
      app-ml-train:
        condition: service_completed_successfully

  app-stream-data:
    image: ${DOCKERHUB_USERNAME}/ml-app-wind-draft:latest
    command: ["python", "entrypoint/app_stream_data.py"]
    volumes:
      - ./data:/app/data
      - ./conf:/app/conf
    networks:
      - ml-app-network
    restart: unless-stopped
    depends_on:
      - mlflow

  kedro-viz:
    image: ${DOCKERHUB_USERNAME}/ml-app-wind-draft:latest
    command: ["kedro", "viz", "--host", "0.0.0.0", "--port", "4141"]
    ports:
      - "4141:4141"
    networks:
      - ml-app-network
    restart: unless-stopped
    depends_on:
      - app-ml-inference

networks:
  ml-app-network:
    driver: bridge
```

**Key differences from local:**
- `image: ${DOCKERHUB_USERNAME}/ml-app-wind-draft:latest` instead of `build:`
- Environment variables are required (no defaults)
- Images are pulled from Docker Hub

### Step 4: Complete Production Docker Compose

Create `docker-compose.yml`:

```yaml
services:
  mlflow:
    image: ${DOCKERHUB_USERNAME}/ml-app-wind-draft:latest
    command: >
      sh -c "mlflow server 
      --host 0.0.0.0 
      --port 5001 
      --default-artifact-root file:///app/mlflow/mlartifacts
      --allowed-hosts '*'
      --cors-allowed-origins '*'"
    ports:
      - "5001:5001"
    volumes:
      - ./mlflow:/app/mlflow
      - ./data:/app/data
      - ./conf:/app/conf
    networks:
      - ml-app-network
    restart: unless-stopped

  app-ui:
    image: ${DOCKERHUB_USERNAME}/ml-app-wind-draft:latest
    command: ["python", "entrypoint/app_ui.py"]
    ports:
      - "8050:8050"
    volumes:
      - ./data:/app/data
      - ./conf:/app/conf
      - ./mlflow:/app/mlflow
    environment:
      - KEDRO_ENV=local
      - MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI:-http://mlflow:5001}
      - MLFLOW_UI_URI=${MLFLOW_UI_URI}
      - DEBUG=False
      - KEDRO_VIZ_URI=${KEDRO_VIZ_URI}
    networks:
      - ml-app-network
    restart: unless-stopped
    depends_on:
      - mlflow

  app-ml-train:
    image: ${DOCKERHUB_USERNAME}/ml-app-wind-draft:latest
    command: ["python", "entrypoint/training.py"]
    volumes:
      - ./data:/app/data
      - ./conf:/app/conf
      - ./mlflow:/app/mlflow
    environment:
      - KEDRO_ENV=local
      - MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI:-http://mlflow:5001}
    networks:
      - ml-app-network
    restart: "no"
    depends_on:
      - mlflow
      - app-ui

  app-ml-inference:
    image: ${DOCKERHUB_USERNAME}/ml-app-wind-draft:latest
    command: ["python", "entrypoint/inference_real_time.py"]
    volumes:
      - ./data:/app/data
      - ./conf:/app/conf
      - ./mlflow:/app/mlflow
    environment:
      - KEDRO_ENV=local
      - MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI:-http://mlflow:5001}
    networks:
      - ml-app-network
    restart: unless-stopped
    depends_on:
      app-ml-train:
        condition: service_completed_successfully

  app-stream-data:
    image: ${DOCKERHUB_USERNAME}/ml-app-wind-draft:latest
    command: ["python", "entrypoint/app_stream_data.py"]
    volumes:
      - ./data:/app/data
      - ./conf:/app/conf
    networks:
      - ml-app-network
    restart: unless-stopped
    depends_on:
      - mlflow

  kedro-viz:
    image: ${DOCKERHUB_USERNAME}/ml-app-wind-draft:latest
    command: ["kedro", "viz", "--host", "0.0.0.0", "--port", "4141"]
    ports:
      - "4141:4141"
    networks:
      - ml-app-network
    restart: unless-stopped
    depends_on:
      - app-ml-inference

networks:
  ml-app-network:
    driver: bridge
```

### Step 5: Running Production/CD Setup

```bash
# Set environment variables (if not using .env file)
export DOCKERHUB_USERNAME=your-dockerhub-username
export MLFLOW_UI_URI=http://your-server-ip:5001
export KEDRO_VIZ_URI=http://your-server-ip:4141

# Pull latest images from Docker Hub
docker compose pull

# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Step 6: CD Pipeline Integration

In your CD pipeline (e.g., GitHub Actions), you would:

1. **Build and push Docker image:**
```yaml
- name: Build and push Docker image
  run: |
    docker build -t ${{ secrets.DOCKERHUB_USERNAME }}/ml-app-wind-draft:latest .
    docker push ${{ secrets.DOCKERHUB_USERNAME }}/ml-app-wind-draft:latest
```

2. **Deploy using docker-compose:**
```yaml
- name: Deploy with docker-compose
  run: |
    export DOCKERHUB_USERNAME=${{ secrets.DOCKERHUB_USERNAME }}
    export MLFLOW_UI_URI=http://${{ secrets.SERVER_IP }}:5001
    export KEDRO_VIZ_URI=http://${{ secrets.SERVER_IP }}:4141
    docker compose pull
    docker compose up -d
```

## Part 6: Service-Specific Configuration

### Training Service (app-ml-train)

**Characteristics:**
- Runs once, then stops (`restart: "no"`)
- Trains model and saves to MLflow
- Must complete before inference can run

**Run manually:**
```bash
docker compose up app-ml-train
```

### Inference Service (app-ml-inference)

**Characteristics:**
- Runs continuously (`restart: unless-stopped`)
- Monitors for new data every configured interval
- Runs inference pipeline when new data detected
- Initializes predictions table automatically

### Data Streaming Service (app-stream-data)

**Characteristics:**
- Streams data point-by-point to database
- Simulates real-time data ingestion
- Required for inference to have data to process

### UI Service (app-ui)

**Characteristics:**
- Web dashboard on port 8050
- Auto-refreshes every configured interval
- Displays predictions, errors, and model info

**Access:** http://localhost:8050 (local) or http://your-server-ip:8050 (production)

### Kedro Viz Service (kedro-viz)

**Characteristics:**
- Pipeline visualization on port 4141
- Shows data pipeline structure
- Uses `kedro viz` command

**Access:** http://localhost:4141 (local) or http://your-server-ip:4141 (production)

## Part 7: Common Workflows

### Workflow 1: Full Pipeline (Training + Inference)

```bash
# Start MLflow
docker compose up -d mlflow

# Run training (waits for MLflow)
docker compose up app-ml-train

# Start inference (waits for training)
docker compose up -d app-ml-inference

# Start data streaming
docker compose up -d app-stream-data

# Start UI
docker compose up app-ui
```

### Workflow 2: Development Mode

```bash
# Start only infrastructure
docker compose -f docker-compose.local.yml up -d mlflow kedro-viz

# Run training/inference locally
kedro run --pipeline training
kedro run --pipeline inference

# Access services
# MLflow: http://localhost:5001
# Kedro Viz: http://localhost:4141
```

### Workflow 3: Production Mode

```bash
# Set environment variables
export DOCKERHUB_USERNAME=your-username
export MLFLOW_UI_URI=http://your-server-ip:5001
export KEDRO_VIZ_URI=http://your-server-ip:4141

# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

## Part 8: Troubleshooting

### Issue 1: "Invalid Host header" in MLflow

**Solution:** Already fixed with `--allowed-hosts '*'` flag in docker-compose files

### Issue 2: Port Already in Use

**Error:** `Bind for 0.0.0.0:5001 failed: port is already allocated`

**Solution:**
```bash
# Find process using port
lsof -i :5001

# Kill process or change port in docker-compose.yml
```

### Issue 3: Services Can't Connect to MLflow

**Check:**
1. MLflow service is running: `docker compose ps`
2. Network is correct: `networks: - ml-app-network`
3. Service name is correct: `http://mlflow:5001` (not `localhost`)

### Issue 4: Volume Permissions

**Issue:** Container can't write to mounted volumes

**Solution:**
```bash
# Fix permissions (macOS/Linux)
chmod -R 777 ./data ./mlflow
```

### Issue 5: Build Fails with "ModuleNotFoundError"

**Cause:** Source code not copied before `uv sync`

**Solution:** Ensure `COPY . .` comes before `RUN uv sync` in Dockerfile

### Issue 6: Environment Variables Not Set

**Error:** Services fail to start in production

**Solution:** Ensure all required environment variables are set:
- `DOCKERHUB_USERNAME`
- `MLFLOW_UI_URI`
- `KEDRO_VIZ_URI`

## Part 9: Best Practices

### 1. Use .dockerignore

Create `.dockerignore` to exclude unnecessary files:

```
.git
.venv
__pycache__
*.pyc
.pytest_cache
notebooks/.ipynb_checkpoints
mlflow/
data/
```

### 2. Health Checks

Add health checks for services:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8050"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 3. Resource Limits

Set resource limits for production:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

### 4. Environment Variables

Use `.env` file for sensitive data and configuration:

```bash
# .env
DOCKERHUB_USERNAME=your-username
MLFLOW_UI_URI=http://your-server-ip:5001
KEDRO_VIZ_URI=http://your-server-ip:4141
MLFLOW_TRACKING_URI=http://mlflow:5001
```

## Part 10: Useful Commands Reference

### Docker Compose Commands

```bash
# Build images (local development)
docker compose -f docker-compose.local.yml build

# Start services
docker compose up
docker compose up -d              # Background
docker compose up <service>       # Specific service

# Pull images (production)
docker compose pull

# Stop services
docker compose down
docker compose stop               # Stop but don't remove
docker compose restart <service>  # Restart service

# View logs
docker compose logs
docker compose logs -f            # Follow logs
docker compose logs <service>     # Specific service

# Execute commands
docker compose exec <service> <command>
docker compose exec app-ui python --version

# Check status
docker compose ps                 # Running services
docker compose ps -a               # All services

# Rebuild and restart
docker compose up --build          # Rebuild and start
docker compose up --build <service> # Rebuild specific service
```

### Docker Commands

```bash
# List containers
docker ps
docker ps -a

# List images
docker images

# Remove containers
docker rm <container_id>
docker rm -f <container_id>       # Force remove

# Remove images
docker rmi <image_id>

# Clean up
docker system prune               # Remove unused resources
docker volume prune                # Remove unused volumes
```

## Summary and Key Concepts

### What You've Learned

1. **Dockerfile Creation**: How to create a Dockerfile for your ML application
2. **Local Development Setup**: Building docker-compose for local development with source code mounting
3. **Production/CD Setup**: Configuring docker-compose for production deployment with pre-built images
4. **Service Configuration**: Setting up MLflow, training, inference, UI, and visualization services
5. **Volume and Network Management**: Managing data persistence and service communication

### Key Takeaways

- **Local development** uses `build:` to compile from source
- **Production/CD** uses `image:` to pull pre-built images
- **Environment variables** are required for production deployment
- **Service dependencies** ensure proper startup order
- **Volume mounts** persist data between container restarts

### Next Steps

- Integrate Docker build and push into CI/CD pipeline
- Add health checks and resource limits
- Set up monitoring and logging
- Consider using Docker Swarm or Kubernetes for orchestration
- Implement secrets management for sensitive data
