# Session 16: Building Real-Time Data Streaming and Application Entrypoints

## Overview

This session covers building real-time data streaming capabilities and creating programmatic entrypoints for running ML pipelines and applications. You'll learn how to:

- Stream data point-by-point to simulate real-time data ingestion
- Create entrypoints for running Kedro pipelines programmatically
- Build real-time monitoring systems that trigger pipelines automatically
- Set up application entrypoints for UI and data management

## Part 1: Understanding Entrypoints

### What are Entrypoints?

Entrypoints are standalone Python scripts that allow you to run your application components programmatically, outside of the Kedro CLI. They're essential for:

- **Production deployment**: Running pipelines in containers or scheduled jobs
- **Integration**: Connecting pipelines with external systems
- **Real-time processing**: Continuously monitoring and triggering pipelines
- **Testing**: Running specific components in isolation

### Entrypoint Structure

All entrypoints follow a similar pattern:

```python
"""Programmatic entrypoint for [purpose]."""

import os
import sys
from pathlib import Path

# Path setup
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))
os.chdir(project_root)

# Your code here

if __name__ == "__main__":
    # Entry point logic
    pass
```

**Key concepts:**
- `Path(__file__).resolve().parents[1]`: Gets project root directory
- `sys.path.insert()`: Adds project paths for imports
- `os.chdir()`: Changes working directory for relative paths

## Part 2: Training Pipeline Entrypoint

### Step 1: Create Training Entrypoint

Create `entrypoint/training.py`:

```python
"""Programmatic entrypoint for running the Kedro training pipeline."""

import os
import sys
import tomllib
from pathlib import Path

from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# Change to project directory so relative paths resolve correctly
os.chdir(project_root)


def run_training_pipeline(
    env: str = "local",
    pipeline_name: str = "training",
) -> None:
    """Run the Kedro training pipeline programmatically."""
    # Extract package name from pyproject.toml
    with open(project_root / "pyproject.toml", "rb") as f:
        package_name = tomllib.load(f)["tool"]["kedro"]["package_name"]

    configure_project(package_name)
    bootstrap_project(project_root)

    with KedroSession.create(project_path=project_root, env=env) as session:
        session.run(pipeline_name=pipeline_name)


if __name__ == "__main__":
    run_training_pipeline()
```

**Key concepts:**
- **`configure_project()`**: Initializes Kedro project configuration
- **`bootstrap_project()`**: Sets up project structure and plugins
- **`KedroSession.create()`**: Creates a session for running pipelines
- **`session.run()`**: Executes the specified pipeline

**Usage:**
```bash
python entrypoint/training.py
```

## Part 3: Inference Pipeline Entrypoint

### Step 1: Create Inference Entrypoint

Create `entrypoint/inference.py`:

```python
"""Programmatic entrypoint for running the Kedro inference pipeline."""

import os
import sys
import tomllib
from pathlib import Path

from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# Change to project directory so relative paths resolve correctly
os.chdir(project_root)


def run_inference_pipeline(
    env: str = "local",
    pipeline_name: str = "inference",
) -> None:
    """Run the Kedro inference pipeline programmatically."""
    # Extract package name from pyproject.toml
    with open(project_root / "pyproject.toml", "rb") as f:
        package_name = tomllib.load(f)["tool"]["kedro"]["package_name"]

    configure_project(package_name)
    bootstrap_project(project_root)

    with KedroSession.create(project_path=project_root, env=env) as session:
        session.run(pipeline_name=pipeline_name)


if __name__ == "__main__":
    run_inference_pipeline()
```

**Usage:**
```bash
python entrypoint/inference.py
```

## Part 4: UI Application Entrypoint

### Step 1: Create UI Entrypoint

### Step 1: Real-Time Training Entrypoint

Create `entrypoint/training_real_time.py`:

```python
"""Programmatic entrypoint for running the Kedro training pipeline periodically."""

import os
import sys
import time
import tomllib
from datetime import datetime
from pathlib import Path

from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from loguru import logger

# Add src directory to path before imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))
sys.path.append(str(project_root))

# Change to project directory so relative paths resolve correctly
os.chdir(project_root)

from app_data_manager.utils import read_config
from common.mlflow_utils import get_latest_model_timestamp

# Read configuration
parameters_path = project_root / "conf" / "base" / "parameters.yml"
config = read_config(parameters_path)

# Read environment variables
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5001")


def run_training_pipeline(
    env: str = "local",
    pipeline_name: str = "training",
) -> None:
    """Run the Kedro training pipeline programmatically."""
    # Extract package name from pyproject.toml
    with open(project_root / "pyproject.toml", "rb") as f:
        package_name = tomllib.load(f)["tool"]["kedro"]["package_name"]

    configure_project(package_name)
    bootstrap_project(project_root)

    with KedroSession.create(project_path=project_root, env=env) as session:
        session.run(pipeline_name=pipeline_name)


def run_training_real_time() -> None:
    """
    Continuously check MLflow for latest model and run training if enough time has passed.

    Configuration is read from parameters.yml under the 'training_real_time' section.
    """
    # Get configuration from parameters.yml
    training_config = config["training_pipeline"]["training_real_time"]
    training_frequency = training_config["training_frequency"]
    check_interval_seconds = training_config["check_frequency"] * 60.0
    env = "local"  # Default Kedro environment
    model_name = config["mlflow"]["registered_model_name"]

    logger.info(
        f"Starting training monitor (checking every {training_config['check_frequency']} minutes, "
        f"training if {training_frequency} minutes passed since last model)..."
    )

    while True:
        try:
            # Get the timestamp of the latest model (champion or challenger)
            latest_timestamp = get_latest_model_timestamp(
                MLFLOW_TRACKING_URI, model_name
            )

            if latest_timestamp is None:
                logger.warning(
                    "No champion or challenger model found. "
                    "Running training to create initial model..."
                )
                logger.info("Starting training pipeline...")
                run_training_pipeline(env=env, pipeline_name="training")
                logger.info("Training completed successfully")
            else:
                # Calculate time elapsed since last model
                time_elapsed = datetime.now() - latest_timestamp
                time_elapsed_minutes = time_elapsed.total_seconds() / 60.0

                if time_elapsed_minutes >= training_frequency:
                    logger.info(
                        f"Time threshold reached ({time_elapsed_minutes:.2f} >= "
                        f"{training_frequency} minutes). Starting training pipeline..."
                    )
                    run_training_pipeline(env=env, pipeline_name="training")
                    logger.info("Training completed successfully")

            # Wait before next check
            time.sleep(check_interval_seconds)

        except Exception as e:
            logger.exception(f"Error during training check: {e}")
            time.sleep(check_interval_seconds)


if __name__ == "__main__":
    run_training_real_time()
```

**Key concepts:**
- **MLflow integration**: Checks for latest model timestamp
- **Time-based triggering**: Runs training only if enough time has passed
- **Configuration-driven**: Uses `parameters.yml` for settings
- **Error handling**: Continues running even if errors occur
- **Logging**: Uses `loguru` for structured logging

**Configuration in `parameters.yml`:**
```yaml
training_pipeline:
  training_real_time:
    training_frequency: 60.0  # Minutes since last model
    check_frequency: 1.0  # Minutes between checks
```

**Usage:**
```bash
python entrypoint/training_real_time.py
```

## Part 8: Real-Time Inference Entrypoint

### Step 1: Create Real-Time Inference Entrypoint

Create `entrypoint/inference_real_time.py`:

```python
"""Programmatic entrypoint for running inference pipeline when new data is available."""

import os
import sys
import time
import tomllib
from pathlib import Path

from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from loguru import logger

# Add src directory to path before imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))
sys.path.append(str(project_root))

# Change to project directory so relative paths resolve correctly
os.chdir(project_root)

from app_data_manager.data_manager import DataManager
from app_data_manager.utils import read_config


def run_inference_pipeline(
    env: str = "local", pipeline_name: str = "inference"
) -> None:
    """Run the Kedro inference pipeline programmatically."""
    # Extract package name from pyproject.toml
    with open(project_root / "pyproject.toml", "rb") as f:
        package_name = tomllib.load(f)["tool"]["kedro"]["package_name"]

    configure_project(package_name)
    bootstrap_project(project_root)

    with KedroSession.create(project_path=project_root, env=env) as session:
        session.run(pipeline_name=pipeline_name)


def run_inference_real_time(env: str = "local") -> None:
    """
    Continuously check for new data and run inference pipeline when new data is available.

    Configuration is read from parameters.yml under the 'inference_pipeline' section.

    Args:
        env: Kedro environment name.
    """
    config = read_config(os.path.join(project_root, "conf", "base", "parameters.yml"))
    data_manager = DataManager(config)

    # Get check frequency from parameters.yml
    inference_config = config["inference_pipeline"]

    # Initialize predictions table if needed
    data_manager.init_predictions_db_table()

    last_processed_timestamp: str | None = None

    while True:
        try:
            # Get latest timestamp from raw_data table
            df = data_manager.get_last_n_points(1, table_name="raw_data")
            latest_timestamp = df.iloc[-1]["Timestamps"]

            if (
                last_processed_timestamp is None
                or latest_timestamp > last_processed_timestamp
            ):
                logger.info(f"New data detected! Latest timestamp: {latest_timestamp}")
                logger.info("Running inference pipeline...")

                # Run inference pipeline
                run_inference_pipeline(env=env, pipeline_name="inference")

                # Update last processed timestamp
                last_processed_timestamp = latest_timestamp
                logger.info(
                    f"Inference completed. Last processed timestamp: {last_processed_timestamp}"
                )
            else:
                logger.debug(f"No new data. Last timestamp: {latest_timestamp}")

            # Wait before next check
            time.sleep(inference_config["inference_frequency"])
        except Exception as e:
            logger.exception(f"Error during inference check: {e}")
            time.sleep(inference_config["inference_frequency"])


if __name__ == "__main__":
    run_inference_real_time()
```

**Key concepts:**
- **Data-driven triggering**: Checks database for new timestamps
- **Timestamp comparison**: Only runs inference when new data is detected
- **State management**: Tracks last processed timestamp
- **Database integration**: Uses `DataManager` to query raw data

**Configuration in `parameters.yml`:**
```yaml
inference_pipeline:
  inference_frequency: 30  # Seconds between checks
  batch_size: 500
```

## Part 5: Application Entrypoints

### Step 1: UI Application Entrypoint

Create `entrypoint/app_ui.py`:

```python
"""Programmatic entrypoint for running the Dash UI application."""

import os
import sys
from pathlib import Path

# Add src and app_ui directories to path before imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "app_ui"))

# Change to project directory so relative paths resolve correctly
os.chdir(project_root)

from app_ui.app import app  # noqa: E402

if __name__ == "__main__":
    # Use debug=False in production/Docker, debug=True for local development
    debug_mode = os.getenv("DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode, use_reloader=False, host="0.0.0.0", port=8050)
```

**Key concepts:**
- **Path setup**: Adds necessary directories to Python path
- **Environment-based configuration**: Uses `DEBUG` environment variable
- **Production-ready**: Disables reloader for production use
- **Network binding**: Binds to `0.0.0.0` for container deployment

**Usage:**
```bash
# Development
DEBUG=True python entrypoint/app_ui.py

# Production
python entrypoint/app_ui.py
```

## Part 5: Data Manager Entrypoint

### Step 1: Create Data Manager Entrypoint

Create `entrypoint/data_manager_app.py`:

```python
"""Programmatic entrypoint for initializing database and loading initial data."""

import os
from pathlib import Path

import pandas as pd

from app_data_manager.data_manager import DataManager
from app_data_manager.utils import read_config

project_root = Path(__file__).resolve().parents[1]
os.chdir(project_root)

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    config = read_config(os.path.join(project_root, "conf", "base", "parameters.yml"))
    data_manager = DataManager(config)

    # Initialize database tables
    data_manager.init_raw_db_table()
    data_manager.init_predictions_db_table()
    
    # Load initial data
    inference_data = pd.read_parquet(
        os.path.join(project_root, "data", "01_raw", "inference_data.parquet")
    )
    data_manager.insert_data_to_db(inference_data, table_name="raw_data")
```

**Key concepts:**
- **Database initialization**: Sets up tables before data insertion
- **Bulk data loading**: Loads entire dataset at once (not streaming)
- **One-time setup**: Useful for initializing test environments

**Usage:**
```bash
python entrypoint/data_manager_app.py
```

## Part 6: Data Streaming Entrypoint

### Step 1: Create Data Streaming Entrypoint

Create `entrypoint/app_stream_data.py`:

```python
"""Programmatic entrypoint for streaming data point-by-point to the database."""

import os
import time
from pathlib import Path

import pandas as pd

from app_data_manager.data_manager import DataManager
from app_data_manager.utils import read_config

project_root = Path(__file__).resolve().parents[1]
os.chdir(project_root)


def stream_data_to_db(
    sleep_seconds: float = 5.0,
    table_name: str = "raw_data",
) -> None:
    """
    Stream data point-by-point to the database with a delay between each insertion.

    Args:
        sleep_seconds: Number of seconds to sleep between each data point insertion.
        table_name: Name of the table to insert data into.
    """
    config = read_config(os.path.join(project_root, "conf", "base", "parameters.yml"))
    data_manager = DataManager(config)

    # Initialize predictions table (only once)
    data_manager.init_predictions_db_table()

    # Load inference data from config
    inference_data_folder = config["data_manager"]["inference_data_folder"]
    inference_data_filename = config["data_manager"]["inference_data_filename"]
    data_path = os.path.join(
        project_root, inference_data_folder, inference_data_filename
    )
    inference_data = pd.read_parquet(data_path)

    while True:
        # Clean database by reinitializing the raw data table
        data_manager.init_raw_db_table()

        # Iterate over each row and insert one at a time
        for idx, row in inference_data.iterrows():
            # Convert single row to DataFrame for insertion
            row_df = row.to_frame().T

            # Insert single row
            data_manager.insert_data_to_db(row_df, table_name=table_name)

            # Sleep before next insertion
            if idx < len(inference_data) - 1:  # Don't sleep after last row
                time.sleep(sleep_seconds)


if __name__ == "__main__":
    stream_data_to_db()
```

**Key concepts:**
- **Point-by-point streaming**: Inserts one row at a time to simulate real-time data
- **Database reinitialization**: Cleans the table before each streaming cycle
- **Configurable delay**: `sleep_seconds` controls the rate of data ingestion
- **Infinite loop**: Continuously streams data in cycles

**Why this approach?**
- Simulates real-world streaming scenarios
- Allows testing of real-time inference pipelines
- Provides controlled data flow for development

**Usage:**
```bash
python entrypoint/app_stream_data.py
```

**What happens:**
1. Database tables are initialized
2. Data is loaded from Parquet file
3. Each row is inserted with a delay
4. Process repeats indefinitely

**Monitoring:**
- Check database to see data accumulating
- Use `DataManager.get_last_n_points()` to verify streaming
- Adjust `sleep_seconds` to control streaming rate

## Part 7: Real-Time Training Entrypoint

### Step 1: Create Real-Time Training Entrypoint

### 1. Path Management

Always set up paths correctly:

```python
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))
os.chdir(project_root)
```

**Why:**
- Ensures imports work correctly
- Makes relative paths resolve properly
- Works in different execution contexts

### 2. Configuration Management

Read configuration from `parameters.yml`:

```python
from app_data_manager.utils import read_config

config = read_config(
    os.path.join(project_root, "conf", "base", "parameters.yml")
)
```

**Benefits:**
- Centralized configuration
- Environment-specific settings
- Easy to modify without code changes

### 3. Error Handling

Use proper exception handling in loops:

```python
while True:
    try:
        # Your logic here
        pass
    except Exception as e:
        logger.exception(f"Error: {e}")
        time.sleep(check_interval)
```

**Why:**
- Prevents crashes in long-running processes
- Allows recovery from transient errors
- Maintains service availability

### 4. Logging

Use structured logging with `loguru`:

```python
from loguru import logger

logger.info("Starting process...")
logger.warning("No model found, creating initial model...")
logger.exception("Error occurred", exc_info=True)
```

**Benefits:**
- Better debugging
- Production monitoring
- Structured log output

### 5. Environment Variables

Use environment variables for deployment-specific settings:

```python
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5001")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

**Why:**
- Different settings for dev/staging/prod
- No code changes needed for deployment
- Security (secrets management)

## Part 10: Testing Entrypoints

### Testing Basic Entrypoints

```bash
# Test training pipeline
python entrypoint/training.py

# Test inference pipeline
python entrypoint/inference.py
```

### Testing Real-Time Entrypoints

```bash
# Terminal 1: Start data streaming
python entrypoint/app_stream_data.py

# Terminal 2: Start real-time inference
python entrypoint/inference_real_time.py

# Terminal 3: Start real-time training (optional)
python entrypoint/training_real_time.py
```

### Testing UI Entrypoint

```bash
# Start UI application
python entrypoint/app_ui.py

# Access at http://localhost:8050
```

## Summary and Key Concepts

### What You've Learned

1. **Entrypoint Structure**: How to create standalone scripts that run Kedro pipelines
2. **Real-Time Streaming**: Simulating point-by-point data ingestion
3. **Monitoring Systems**: Building continuous monitoring for training and inference
4. **Application Entrypoints**: Creating entrypoints for UI and data management
5. **Best Practices**: Path management, configuration, error handling, logging

### Key Takeaways

- **Entrypoints enable programmatic execution** of pipelines outside Kedro CLI
- **Real-time systems** require continuous monitoring and state management
- **Configuration-driven design** makes systems flexible and maintainable
- **Proper error handling** ensures long-running processes stay alive
- **Environment variables** enable deployment flexibility

### Next Steps

- Integrate entrypoints with orchestration tools (Prefect, Airflow)
- Add health checks and monitoring endpoints
- Implement graceful shutdown handling
- Add retry logic for transient failures
- Create deployment configurations for different environments

