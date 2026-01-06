# Session 19: ML Pipeline Orchestration with Prefect

## Overview

This session covers orchestrating your ML pipelines using Prefect. You'll learn how to:

- Run Prefect flows locally without Prefect server (direct execution)
- Deploy flows using Prefect server and `flow.serve()`
- Set up real-time training and inference orchestration
- Monitor and manage pipeline executions
- Troubleshoot common Prefect issues

## Prerequisites

- Python 3.11 or 3.12 installed
- Your ML application working locally (Kedro pipelines)
- Prefect installed (already in `pyproject.toml`)
- Basic understanding of Python and command line

## Part 1: Understanding Prefect

### What is Prefect?

Prefect is a workflow orchestration tool that helps you:
- **Schedule** pipelines to run at specific intervals
- **Monitor** pipeline execution and view logs
- **Retry** failed runs automatically
- **Scale** by running workers on multiple machines
- **Track** execution history and performance metrics

### Key Concepts

#### 1. **Flows** (`@flow`)
- Top-level functions that define a workflow
- Can contain multiple tasks
- Handle orchestration logic

#### 2. **Tasks** (`@task`)
- Individual units of work
- Can be retried independently
- Represent discrete operations (e.g., "run training pipeline")

#### 3. **Deployments**
- Configuration that defines how a flow should run
- Includes: schedule, parameters, work queue assignment
- Registered with Prefect server

#### 4. **Work Pools and Queues**
- Work pools: Logical groups for organizing workers
- Work queues: Queues that hold scheduled flow runs
- Workers pull jobs from queues

#### 5. **Prefect Server**
- API server and database
- Stores deployments, run history, logs
- Provides UI at http://localhost:4200

## Part 2: Running Prefect Locally Without Serve

### Step 1: Create a Simple Training Flow

Create `entrypoint/prefect/training_flow.py`:

```python
"""Prefect flow for training pipeline orchestration."""

import os
import sys
import tomllib
from datetime import datetime, timedelta
from pathlib import Path

from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from loguru import logger
from prefect import flow, task

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))
sys.path.append(str(project_root))
os.chdir(project_root)

from app_data_manager.utils import read_config
from common.mlflow_utils import get_latest_model_timestamp

# Read configuration
parameters_path = project_root / "conf" / "base" / "parameters.yml"
config = read_config(parameters_path)

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5001")


@task(name="check-latest-model-timestamp")
def check_latest_model_timestamp_task(
    mlflow_tracking_uri: str, model_name: str
) -> datetime | None:
    """Check MLflow for the latest model timestamp (champion or challenger)."""
    return get_latest_model_timestamp(mlflow_tracking_uri, model_name)


@task(name="should-train")
def should_train_task(
    latest_timestamp: datetime | None, training_frequency: float
) -> bool:
    """
    Determine if training should run based on the latest model timestamp.

    Returns True if:
    - No model exists (latest_timestamp is None), or
    - Enough time has passed since the last model (>= training_frequency minutes)
    """
    if latest_timestamp is None:
        logger.warning(
            "No champion or challenger model found. Training should run to create initial model."
        )
        return True

    time_elapsed = datetime.now() - latest_timestamp
    time_elapsed_minutes = time_elapsed.total_seconds() / 60.0

    if time_elapsed_minutes >= training_frequency:
        logger.info(
            f"Time threshold reached ({time_elapsed_minutes:.2f} >= "
            f"{training_frequency} minutes). Training should run."
        )
        return True

    logger.info(
        f"Time threshold not reached ({time_elapsed_minutes:.2f} < "
        f"{training_frequency} minutes). Skipping training."
    )
    return False


@task(name="training-task")
def training_task(env: str = "local", pipeline_name: str = "training"):
    """Prefect task to run the Kedro training pipeline."""
    logger.info("Starting training pipeline...")
    # Extract package name from pyproject.toml
    with open(project_root / "pyproject.toml", "rb") as f:
        package_name = tomllib.load(f)["tool"]["kedro"]["package_name"]

    configure_project(package_name)
    bootstrap_project(project_root)

    with KedroSession.create(project_path=project_root, env=env) as session:
        session.run(pipeline_name=pipeline_name)

    logger.info("Training completed successfully")


@flow(name="training-flow")
def training_flow(env: str = "local"):
    """
    Prefect flow for training that checks MLflow and runs training if needed.

    Configuration is read from parameters.yml under the 'training_real_time' section.
    """
    # Get configuration from parameters.yml
    training_config = config["training_pipeline"]["training_real_time"]
    training_frequency = training_config["training_frequency"]
    model_name = config["mlflow"]["registered_model_name"]

    logger.info(
        f"Training flow started (training if {training_frequency} minutes passed since last model)..."
    )

    # Check for latest model timestamp
    latest_timestamp = check_latest_model_timestamp_task(
        MLFLOW_TRACKING_URI, model_name
    )

    # Decide if training should run
    should_train = should_train_task(latest_timestamp, training_frequency)

    # Run training if needed
    if should_train:
        training_task(env=env)
    else:
        logger.info("Training skipped - not enough time has passed since last model.")


if __name__ == "__main__":
    # Direct execution without Prefect server
    training_flow(env="local")
```

**Key points:**
- No Prefect server needed
- Flow runs directly when script is executed
- Tasks execute in sequence
- Perfect for testing and development

### Step 2: Run the Flow Directly

1. **Set environment variables (optional):**
   ```bash
   export MLFLOW_TRACKING_URI=http://localhost:5001
   export KEDRO_ENV=local
   ```

2. **Run the flow:**
   ```bash
   cd /path/to/ml-app-wind-draft
   python entrypoint/prefect/training_flow.py
   ```

**What happens:**
- Flow executes immediately
- You see Kedro pipeline execution logs
- Flow completes and script exits
- No Prefect server or worker needed

**Expected output:**
```
Training flow started (training if 60.0 minutes passed since last model)...
Time threshold reached (120.5 >= 60.0 minutes). Training should run.
Starting training pipeline...
[Kedro pipeline execution logs...]
Training completed successfully
```

### Step 3: Create a Simple Inference Flow

Create `entrypoint/prefect/inference_flow.py`:

```python
"""Prefect flow for inference pipeline orchestration."""

import os
import sys
import tomllib
from datetime import datetime
from pathlib import Path

from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from loguru import logger
from prefect import flow, task

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))
sys.path.append(str(project_root))
os.chdir(project_root)

from app_data_manager.data_manager import DataManager
from app_data_manager.utils import read_config

# Read configuration
parameters_path = project_root / "conf" / "base" / "parameters.yml"
config = read_config(parameters_path)


@task(name="get-latest-raw-timestamp")
def get_latest_raw_timestamp_task(table_name: str = "raw_data") -> str | None:
    """Get the latest timestamp from the raw_data table."""
    try:
        data_manager = DataManager(config)
        df = data_manager.get_last_n_points(1, table_name=table_name)
        if df.empty:
            return None
        return str(df.iloc[-1]["Timestamps"])
    except Exception as e:
        logger.error(f"Error getting latest raw timestamp: {e}")
        return None


@task(name="get-latest-prediction-timestamp")
def get_latest_prediction_timestamp_task(
    table_name: str = "predictions",
) -> datetime | None:
    """Get the latest timestamp from the predictions table as datetime."""
    try:
        data_manager = DataManager(config)
        df = data_manager.get_last_n_points(1, table_name=table_name)
        if df.empty:
            return None
        timestamp_str = str(df.iloc[-1]["Timestamps"])
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Error getting latest prediction timestamp: {e}")
        return None


@task(name="should-run-inference")
def should_run_inference_task(
    latest_raw_timestamp: str | None,
    last_processed_timestamp: datetime | None,
    inference_frequency: float,
) -> bool:
    """Determine if inference should run based on timestamp comparison and frequency."""
    if latest_raw_timestamp is None:
        logger.debug("No data in raw_data table yet. Skipping inference.")
        return False

    # Check if there's new data
    has_new_data = False
    if last_processed_timestamp is None:
        has_new_data = True
        logger.info(
            f"No predictions found. New data detected! Latest timestamp: {latest_raw_timestamp}"
        )
    else:
        try:
            last_processed_str = last_processed_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if latest_raw_timestamp > last_processed_str:
                has_new_data = True
        except Exception as e:
            logger.warning(f"Error comparing timestamps: {e}. Assuming new data exists.")
            has_new_data = True

    if not has_new_data:
        logger.debug(f"No new data. Last timestamp: {latest_raw_timestamp}")
        return False

    # Check if enough time has passed since last inference
    if last_processed_timestamp is None:
        return True

    time_elapsed = datetime.now() - last_processed_timestamp
    time_elapsed_seconds = time_elapsed.total_seconds()

    if time_elapsed_seconds >= inference_frequency:
        logger.info(
            f"Time threshold reached ({time_elapsed_seconds:.2f} >= "
            f"{inference_frequency} seconds). Inference should run."
        )
        return True

    logger.info(
        f"Time threshold not reached ({time_elapsed_seconds:.2f} < "
        f"{inference_frequency} seconds). Skipping inference."
    )
    return False


@task(name="inference-task")
def inference_task(env: str = "local", pipeline_name: str = "inference"):
    """Prefect task to run the Kedro inference pipeline."""
    logger.info("Starting inference pipeline...")
    with open(project_root / "pyproject.toml", "rb") as f:
        package_name = tomllib.load(f)["tool"]["kedro"]["package_name"]

    configure_project(package_name)
    bootstrap_project(project_root)

    with KedroSession.create(project_path=project_root, env=env) as session:
        session.run(pipeline_name=pipeline_name)

    logger.info("Inference completed successfully")


@task(name="init-predictions-table")
def init_predictions_table_task():
    """Initialize predictions table if needed."""
    data_manager = DataManager(config)
    data_manager.init_predictions_db_table()


@flow(name="inference-flow")
def inference_flow(env: str = "local"):
    """
    Prefect flow for inference that checks for new data and runs inference if needed.

    Configuration is read from parameters.yml under the 'inference_pipeline' section.
    """
    # Get configuration from parameters.yml
    inference_config = config["inference_pipeline"]
    inference_frequency = inference_config["inference_frequency"]

    logger.info(
        f"Inference flow started (inference if {inference_frequency} seconds passed since last inference and new data available)..."
    )

    # Initialize predictions table
    init_predictions_table_task()

    # Get latest timestamps
    latest_raw_timestamp = get_latest_raw_timestamp_task("raw_data")
    last_processed_timestamp = get_latest_prediction_timestamp_task("predictions")

    # Decide if inference should run
    should_run = should_run_inference_task(
        latest_raw_timestamp, last_processed_timestamp, inference_frequency
    )

    # Run inference if needed
    if should_run:
        inference_task(env=env)
        logger.info(
            f"Inference completed. Last processed timestamp: {latest_raw_timestamp}"
        )
    else:
        logger.info("Inference skipped - conditions not met.")


if __name__ == "__main__":
    # Direct execution without Prefect server
    inference_flow(env="local")
```

### Step 4: Test Both Flows

1. **Test training flow:**
   ```bash
   python entrypoint/prefect/training_flow.py
   ```

2. **Test inference flow:**
   ```bash
   python entrypoint/prefect/inference_flow.py
   ```

**Benefits of direct execution:**
- No setup required (no Prefect server)
- Fast iteration during development
- Easy debugging
- Immediate feedback

## Part 3: Adding Prefect Serve

### Step 1: Install and Start Prefect Server

1. **Install Prefect (if not already installed):**
   ```bash
   uv add prefect
   ```

2. **Start Prefect server:**
   ```bash
   prefect server start
   ```

**Keep this terminal running!** You should see:
```
Starting Prefect API server at http://127.0.0.1:4200/api
Starting Prefect UI at http://127.0.0.1:4200
```

3. **Access Prefect UI:**
   - Open browser: http://localhost:4200
   - You should see the Prefect dashboard

### Step 2: Set Up Work Pool and Queue

**Terminal 2:**
```bash
export PREFECT_API_URL=http://127.0.0.1:4200/api

# Create work pool (ignore error if already exists)
prefect work-pool create default-worker-pool --type process 2>/dev/null || true

# Create work queues (ignore errors if already exist)
prefect work-queue create training-queue --pool default-worker-pool 2>/dev/null || true
prefect work-queue create inference-queue --pool default-worker-pool 2>/dev/null || true
```

**Verify:**
```bash
prefect work-pool ls
prefect work-queue ls
```

### Step 3: Start Prefect Worker

**Terminal 3:**
```bash
export PREFECT_API_URL=http://127.0.0.1:4200/api

prefect worker start \
  --pool default-worker-pool \
  --work-queue training-queue \
  --work-queue inference-queue
```

**Keep this running!** The worker will:
- Connect to Prefect server
- Listen to the specified queues
- Execute scheduled flow runs

**Expected output:**
```
Connected to Prefect server at http://127.0.0.1:4200/api
Polling for runs from queues: training-queue, inference-queue
```

### Step 4: Update Training Flow to Use Serve

Update `entrypoint/prefect/training_flow.py`:

```python
# ... existing code ...

if __name__ == "__main__":
    os.environ.setdefault("PREFECT_API_URL", "http://127.0.0.1:4200/api")

    # Get check frequency from parameters.yml
    training_config = config["training_pipeline"]["training_real_time"]
    check_frequency_minutes = training_config["check_frequency"]

    training_flow.serve(
        name="training-flow",
        interval=timedelta(minutes=check_frequency_minutes),
        parameters={"env": os.getenv("KEDRO_ENV", "local")},
    )

    # Comment out direct execution for deployment
    # training_flow(env="local")
```

**Key changes:**
- Added `flow.serve()` instead of direct execution
- Set `PREFECT_API_URL` environment variable
- Configured interval from `parameters.yml`
- Deployment runs continuously

### Step 5: Update Inference Flow to Use Serve

Update `entrypoint/prefect/inference_flow.py`:

```python
# ... existing code ...

if __name__ == "__main__":
    os.environ.setdefault("PREFECT_API_URL", "http://127.0.0.1:4200/api")

    inference_flow.serve(
        name="inference-flow",
        interval=timedelta(seconds=config["inference_pipeline"]["inference_frequency"]),
        parameters={"env": os.getenv("KEDRO_ENV", "local")},
    )

    # Comment out direct execution for deployment
    # inference_flow(env="local")
```

### Step 6: Deploy Flows

**Terminal 4 (Training):**
```bash
cd /path/to/ml-app-wind-draft
export PREFECT_API_URL=http://127.0.0.1:4200/api
export KEDRO_ENV=local
export MLFLOW_TRACKING_URI=http://localhost:5001

python entrypoint/prefect/training_flow.py
```

**Terminal 5 (Inference):**
```bash
cd /path/to/ml-app-wind-draft
export PREFECT_API_URL=http://127.0.0.1:4200/api
export KEDRO_ENV=local
export MLFLOW_TRACKING_URI=http://localhost:5001

python entrypoint/prefect/inference_flow.py
```

**What happens:**
- Scripts register deployments with Prefect server
- Deployments become active and scheduled
- Scripts continue running (serving the deployments)
- Worker picks up scheduled runs and executes them

**Expected output:**
```
Serving deployment 'training-flow'...
Press CTRL+C to exit.
```

### Step 7: Monitor in Prefect UI

1. **Open Prefect UI:** http://localhost:4200

2. **View deployments:**
   - Click "Deployments" in sidebar
   - You should see `training-flow` and `inference-flow`

3. **Monitor flow runs:**
   - Click on a deployment
   - View "Flow Runs" tab
   - See execution history and logs

4. **Check worker status:**
   - Click "Work Pools" in sidebar
   - See worker status and queue information

## Part 4: Real-Time Training and Inference Orchestration

### Step 1: Understanding Real-Time Orchestration

With `flow.serve()`, Prefect:
- Continuously monitors schedules
- Triggers flow runs at specified intervals
- Executes flows through workers
- Tracks execution history

**Training flow:**
- Checks MLflow for latest model timestamp
- Runs training if enough time has passed
- Scheduled based on `check_frequency` from `parameters.yml`

**Inference flow:**
- Checks database for new data
- Compares timestamps to detect new data
- Runs inference if new data and enough time passed
- Scheduled based on `inference_frequency` from `parameters.yml`

### Step 2: Configuration in parameters.yml

Ensure your `conf/base/parameters.yml` has:

```yaml
training_pipeline:
  training_real_time:
    training_frequency: 60.0  # Minutes since last model before triggering training
    check_frequency: 1.0      # Minutes between checks

inference_pipeline:
  inference_frequency: 30     # Seconds since last inference before triggering
  batch_size: 500
```

### Step 3: Complete Setup Workflow

**Terminal 1: Prefect Server**
```bash
prefect server start
```

**Terminal 2: Setup (One-time)**
```bash
export PREFECT_API_URL=http://127.0.0.1:4200/api
prefect work-pool create default-worker-pool --type process 2>/dev/null || true
prefect work-queue create training-queue --pool default-worker-pool 2>/dev/null || true
prefect work-queue create inference-queue --pool default-worker-pool 2>/dev/null || true
```

**Terminal 3: Worker**
```bash
export PREFECT_API_URL=http://127.0.0.1:4200/api
prefect worker start \
  --pool default-worker-pool \
  --work-queue training-queue \
  --work-queue inference-queue
```

**Terminal 4: Deploy Training Flow**
```bash
export PREFECT_API_URL=http://127.0.0.1:4200/api
export KEDRO_ENV=local
export MLFLOW_TRACKING_URI=http://localhost:5001
python entrypoint/prefect/training_flow.py
```

**Terminal 5: Deploy Inference Flow**
```bash
export PREFECT_API_URL=http://127.0.0.1:4200/api
export KEDRO_ENV=local
export MLFLOW_TRACKING_URI=http://localhost:5001
python entrypoint/prefect/inference_flow.py
```

### Step 4: Verify Real-Time Orchestration

1. **Check Prefect UI:**
   - Go to http://localhost:4200
   - View "Flow Runs" to see scheduled executions
   - Check logs for each run

2. **Monitor execution:**
   - Training flow runs every `check_frequency` minutes
   - Checks if training is needed based on model age
   - Inference flow runs every `inference_frequency` seconds
   - Checks for new data and runs inference if needed

3. **View logs:**
   - Click on a flow run in Prefect UI
   - View "Logs" tab for detailed execution logs
   - See task-level execution details

## Part 5: Monitoring and Management

### Prefect UI Features

**Dashboard:**
- Overview of recent runs
- Success/failure rates
- Quick access to recent flow runs

**Deployments:**
- View all registered deployments
- See schedule and configuration
- Manual trigger option

**Flow Runs:**
- Execution history
- Status (Running, Completed, Failed)
- Detailed logs and timing

**Work Pools:**
- Worker pool status
- Active workers
- Queue information

### CLI Commands

```bash
# List deployments
prefect deployment ls

# Inspect a specific deployment
prefect deployment inspect training-flow/training-flow

# List flow runs
prefect flow-run ls --limit 10

# Inspect a flow run
prefect flow-run inspect <flow-run-id>

# List work pools
prefect work-pool ls

# List work queues
prefect work-queue ls
```

### Managing Workers

**Find running workers:**
```bash
ps aux | grep "[p]refect worker"
```

**Stop all workers:**
```bash
pkill -f "prefect worker"
```

## Part 6: Troubleshooting

### Issue 1: Flow Not Executing

**Symptoms:**
- Deployment registered but no runs appearing
- Worker running but idle

**Solutions:**
1. Check worker is connected:
   ```bash
   prefect work-pool inspect default-worker-pool
   ```

2. Verify queue names match:
   - Check deployment queue name matches worker queue name

3. Check worker logs:
   - Look at worker terminal output
   - Should show "Polling for runs from queues: ..."

### Issue 2: Prefect Server Connection Refused

**Symptoms:**
- `ConnectionRefusedError` when deploying
- `PREFECT_API_URL` errors

**Solutions:**
1. Start Prefect server first:
   ```bash
   prefect server start
   ```

2. Set environment variable:
   ```bash
   export PREFECT_API_URL=http://127.0.0.1:4200/api
   ```

3. Wait for server to fully start before running deployment script

### Issue 3: Import Errors

**Symptoms:**
- `ModuleNotFoundError` when flow runs
- Path resolution errors

**Solutions:**
1. Verify path calculation:
   ```python
   # From entrypoint/prefect/training_flow.py
   project_root = Path(__file__).resolve().parents[2]  # Goes up 2 levels
   ```

2. Test locally first using direct execution

3. Check working directory:
   ```python
   os.chdir(project_root)  # Must be set before imports
   ```

### Issue 4: Flow Run Fails Immediately

**Possible Causes:**
1. Python path issues
2. Missing dependencies
3. Kedro project not configured

**Solutions:**
1. Verify all dependencies installed:
   ```bash
   uv sync
   ```

2. Test flow locally first:
   ```python
   # Uncomment direct execution
   training_flow(env="local")
   ```

3. Check Prefect UI logs for detailed error messages

## Part 7: Best Practices

### 1. Always Test Locally First

```python
# Test with direct execution
if __name__ == "__main__":
    training_flow(env="local")

# Deploy only after testing works
# if __name__ == "__main__":
#     training_flow.serve(...)
```

### 2. Use Descriptive Names

```python
# Good
name="training-flow"
tags=["training", "production"]

# Bad
name="train"
tags=["t"]
```

### 3. Set Appropriate Intervals

- **Training**: Usually daily or weekly (longer intervals)
- **Inference**: Often minutes or hours (shorter intervals)
- **Testing**: Use short intervals (1-5 minutes)

### 4. Monitor Regularly

- Check Prefect UI for failed runs
- Review logs for errors
- Monitor worker status

### 5. Environment Variables

- Set in deployment scripts
- Use `.env` files for local development
- Never hardcode sensitive values

## Summary and Key Concepts

### What You've Learned

1. **Direct Execution**: Running Prefect flows without server for testing
2. **Prefect Server**: Setting up server, workers, and queues
3. **Flow Deployment**: Using `flow.serve()` for continuous orchestration
4. **Real-Time Orchestration**: Automating training and inference pipelines
5. **Monitoring**: Using Prefect UI and CLI for management

### Key Takeaways

- **Direct execution** is perfect for testing and development
- **Prefect server** enables scheduling and monitoring
- **`flow.serve()`** provides continuous orchestration
- **Workers** execute scheduled flow runs
- **Prefect UI** provides comprehensive monitoring

### Next Steps

- Explore Prefect UI features (filters, search, run details)
- Experiment with different schedules
- Add retry logic and error handling
- Set up separate workers for different workloads
- Consider Prefect Cloud for production deployments
- Integrate with monitoring/alerting systems

