# Notes:
- pre-build docker image before the session
- add `print` statements in all `entrypoint` files
- Don't push to Dockerhub, because it might make the video connection slow

# Introduction

### Introduce Docker with slides including `How Docker solves “Works on my machine” problem`

### Install Docker
- https://docs.docker.com/desktop/setup/install

### What we need to Dockerize, go through the application architecture again.

## Prerequisites
- Docker Desktop installed and running
- Basic understanding of Docker concepts (containers, images, volumes)
- Your ML application is working locally


### Create Dockerfile
### Show the slides 
- `Docker Image vs Container`
- `What is Docker Registry`
- `Dockerfile - what is it and what’s inside`
- 
### Create Dockerfile and add this:
```dockerfile
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
```

### Now, we can build a Docker image of your apps
```bash
docker build .
```

### Once built, we can check our images
```bash
docker images
```

### We can run a container
```dockerfile
docker run #IMAGE ID 
```
### We can also build an image with a tag
```bash
docker build -t my-app:1.0 .
```
Why to use tags:
- Version Control
- Can run easier like:
```bash
docker run my-app:1.0
```

### It's great, but we have many applications and somehow we need to run them all

### For this, we use docker-compose. Show the slide `Docker-compose: what is it and what’s inside`

### We already mentioned Docker Volumes. Introduce it with the slide: `Docker Volumes in ML Systems`

### Create file `docker-compose.yml`

### Create first service of Docker compose:
```yaml
services:
  # =============================================================================
  # DATA STREAMING SERVICE
  # =============================================================================
  app-stream-data:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["python", "entrypoints/app_stream_data.py"]
    volumes:
      - app_data:/app/data
      - ./conf:/app/conf # bind mount the configuration files
    environment:
    - PYTHONUNBUFFERED=1 # ensure we see python output in real time

volumes:
  app_data:
```

### Say that things that we can edit manually often are better specified as bind mounts
A bind mount connects a folder (or file) from your computer directly into a container.
If you change a file on your laptop → the container sees the change instantly.


### Run 
```bash
docker compose build
```

### Run
```bash
docker compose up
```

### To check containers, run
```bash
docker ps
```

### Add MLflow Server and update volumes
```yaml
mlflow_server:
 build:
   context: .
   dockerfile: Dockerfile
 command: >
   sh -c "mlflow server
   --host 0.0.0.0
   --port 8080
   --backend-store-uri sqlite:///mlflow/mlflow.db
   --default-artifact-root file:///app/mlflow/artifacts
   --serve-artifacts
   --allowed-hosts '*'
   --cors-allowed-origins '*'"
 ports:
   - "8080:8080"
 volumes:
   - mlflow_data:/app/mlflow
   - app_data:/app/data
   - ./conf:/app/conf
```

and

```yaml
volumes:
  app_data:
  mlflow_data:
```


### Add Training app and run `docker compose up`
```yaml
app-ml-train:
 build:
   context: .
   dockerfile: Dockerfile
 command: ["python", "entrypoints/training.py"]
 volumes:
   - mlflow_data:/app/mlflow
   - app_data:/app/data
   - ./conf:/app/conf
 environment:
   - MLFLOW_TRACKING_URI=http://mlflow_server:8080
 depends_on:
   - mlflow_server
   - app-stream-data
```

### Check Mlflow server `localhost:8080`

### Add Real-time inference app and run `docker compose up`
```yaml
app-ml-inference:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["python", "entrypoints/inference_real_time.py"]
    volumes:
      - mlflow_data:/app/mlflow
      - app_data:/app/data
      - ./conf:/app/conf
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow_server:8080
    depends_on:
      app-ml-train:
        condition: service_completed_successfully
```

### Add UI app
```yaml
app-ui:
    build:
      context: .                    # Build context is the project root
      dockerfile: Dockerfile        # Use the shared Dockerfile
    command: ["python", "entrypoints/app_ui.py"]  # Run the Dash UI app
    ports:
      - "8050:8050"                 # Expose port 8050 for web access
    volumes:
      - mlflow_data:/app/mlflow
      - app_data:/app/data
      - ./conf:/app/conf
    environment:
      - KEDRO_ENV=local
      - MLFLOW_TRACKING_URI=http://mlflow:8080
      - MLFLOW_UI_URI=http://mlflow:8080
      - DEBUG=False
      - KEDRO_VIZ_URI=http://localhost:4141
    depends_on:
      - mlflow_server
      - app-stream-data
```
# Notes:
- pre-build docker image before the session
- add `print` statements in all `entrypoint` files

# Introduction

### Introduce Docker with slides including `How Docker solves “Works on my machine” problem`

### Install Docker
- https://docs.docker.com/desktop/setup/install

### What we need to Dockerize, go through the application architecture again.

## Prerequisites
- Docker Desktop installed and running
- Basic understanding of Docker concepts (containers, images, volumes)
- Your ML application is working locally


### Create Dockerfile
### Show the slides 
- `Docker Image vs Container`
- `What is Docker Registry`
- `Dockerfile - what is it and what’s inside`
- 
### Create Dockerfile and add this:
```dockerfile
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
```

### Now, we can build a Docker image of your apps
```bash
docker build .
```

### Once built, we can check our images
```bash
docker images
```

### We can run a container
```dockerfile
docker run #IMAGE ID 
```
### We can also build an image with a tag
```bash
docker build -t my-app:1.0 .
```
Why to use tags:
- Version Control
- Can run easier like:
```bash
docker run my-app:1.0
```

### It's great, but we have many applications and somehow we need to run them all

### For this, we use docker-compose. Show the slide `Docker-compose: what is it and what’s inside`

### We already mentioned Docker Volumes. Introduce it with the slide: `Docker Volumes in ML Systems`

### Create file `docker-compose.yml`

### Create first service of Docker compose:
```yaml
services:
  # =============================================================================
  # DATA STREAMING SERVICE
  # =============================================================================
  app-stream-data:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["python", "entrypoints/app_stream_data.py"]
    volumes:
      - app_data:/app/data
      - ./conf:/app/conf # bind mount the configuration files
    environment:
    - PYTHONUNBUFFERED=1 # ensure we see python output in real time

volumes:
  app_data:
```

### Say that things that we can edit manually often are better specified as bind mounts
A bind mount connects a folder (or file) from your computer directly into a container.
If you change a file on your laptop → the container sees the change instantly.


### Run 
```bash
docker compose build
```

### Run
```bash
docker compose up
```

### To check containers, run
```bash
docker ps
```

### Add MLflow Server and update volumes
```yaml
mlflow_server:
 build:
   context: .
   dockerfile: Dockerfile
 command: >
   sh -c "mlflow server
   --host 0.0.0.0
   --port 8080
   --backend-store-uri sqlite:///mlflow/mlflow.db
   --default-artifact-root file:///app/mlflow/artifacts
   --serve-artifacts
   --allowed-hosts '*'
   --cors-allowed-origins '*'"
 ports:
   - "8080:8080"
 volumes:
   - mlflow_data:/app/mlflow
   - app_data:/app/data
   - ./conf:/app/conf
```

and

```yaml
volumes:
  app_data:
  mlflow_data:
```


### Add Training app and run `docker compose up`
```yaml
app-ml-train:
 build:
   context: .
   dockerfile: Dockerfile
 command: ["python", "entrypoints/training.py"]
 volumes:
   - mlflow_data:/app/mlflow
   - app_data:/app/data
   - ./conf:/app/conf
 environment:
   - MLFLOW_TRACKING_URI=http://mlflow_server:8080
 depends_on:
   - mlflow_server
   - app-stream-data
```

### Check Mlflow server `localhost:8080`

### Add Real-time inference app and run `docker compose up`
```yaml
app-ml-inference:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["python", "entrypoints/inference_real_time.py"]
    volumes:
      - mlflow_data:/app/mlflow
      - app_data:/app/data
      - ./conf:/app/conf
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow_server:8080
    depends_on:
      app-ml-train:
        condition: service_completed_successfully
```

### Add UI app
```yaml
app-ui:
    build:
      context: .                    # Build context is the project root
      dockerfile: Dockerfile        # Use the shared Dockerfile
    command: ["python", "entrypoints/app_ui.py"]  # Run the Dash UI app
    ports:
      - "8050:8050"                 # Expose port 8050 for web access
    volumes:
      - mlflow_data:/app/mlflow
      - app_data:/app/data
      - ./conf:/app/conf
    environment:
      - KEDRO_ENV=local
      - MLFLOW_TRACKING_URI=http://mlflow:8080
      - MLFLOW_UI_URI=http://mlflow:8080
      - DEBUG=False
      - KEDRO_VIZ_URI=http://localhost:4141
    depends_on:
      - mlflow_server
      - app-stream-data
```

### Before running, add kedro viz
```yaml
kedro-viz:
    build:
      context: .                    # Build context is the project root
      dockerfile: Dockerfile        # Use the shared Dockerfile
    command: ["kedro", "viz", "--host", "0.0.0.0", "--port", "4141"]
    ports:
      - "4141:4141"                 # Expose port 4141 for Kedro Viz UI
    depends_on:
      - app-ml-inference # Wait for inference to be ready
```

### Run
```bash
docker compose up
```

# Docker Registry

### Before running, add kedro viz
```yaml
kedro-viz:
    build:
      context: .                    # Build context is the project root
      dockerfile: Dockerfile        # Use the shared Dockerfile
    command: ["kedro", "viz", "--host", "0.0.0.0", "--port", "4141"]
    ports:
      - "4141:4141"                 # Expose port 4141 for Kedro Viz UI
    depends_on:
      - app-ml-inference # Wait for inference to be ready
```

### Run
```bash
docker compose up
```

# Docker Registry
### Create Dockerhub account and enter
### Login to Dockerhub
```bash
docker login
```

### Press Enter to confirm login

### Build image with `username/repository:tag`
```bash
docker build -t turbine-anomaly:latest .
```

### Add Dockerhub tag
```bash
docker tag turbine-anomaly:latest YOUR_USERNAME/myapp:1.0
```
 - Example
```bash
docker tag turbine-anomaly:latest timurbikmukhametov/turbine-anomaly:latest
```

### Push to Docker Registry
```bash
docker push timurbikmukhametov/turbine-anomaly:latest
```