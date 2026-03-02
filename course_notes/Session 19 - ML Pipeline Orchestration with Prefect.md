# Intro
### Present the slides
- `What is ML Pipeline Orchestration?`
- `How ML Pipeline Orchestrators Work?`
- `Prefect Orchestrator` and `Prefect vs Airflow`
- `Main Prefect Definitions`

# Training flow
### Add prefect to the environment
```bash
uv add prefect
```

### Create a test of reading the re-training trigger data
```python
import os
import pandas as pd
from pathlib import Path
from typing import Any
from prefect import task, flow
from app_data_manager.data_manager import DataManager
from app_data_manager.utils import read_config


project_root = Path(__file__).resolve().parents[2]
os.chdir(project_root)

config = read_config(os.path.join(project_root, "conf", "base", "parameters.yml"))
config_data_manager = config["data_manager"]

@task(name="load_retraining_trigger_data")
def load_retraining_trigger_data(config_data_manager: dict[str, Any]) -> pd.DataFrame:
    """
    Load the last n points from the retraining trigger table.
    """
    data_manager = DataManager(config_data_manager)
    retraining_trigger_df = data_manager.get_last_n_points(
        n=10,
        table_name=config_data_manager["retraining_trigger_table_name"]
        )
    print(retraining_trigger_df)
    return retraining_trigger_df
```

### Add a flow:
```python
@flow(name="training_flow", log_prints=True)
def training_flow(config_data_manager: dict[str, Any]):
    retraining_trigger_df = load_retraining_trigger_data(config_data_manager)

if __name__ == "__main__":
    training_flow(config_data_manager=config_data_manager)
```

### To run prefect, first we need to start the server
```bash
prefect server start
```

### Run `python src/prefect_orchestrator/training_flow.py`

### Go to Prefect and show:
- Dashboard
- Runs
- Flows

### Let's add pipeline training task
```python
from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
import tomllib


@task(name="run_training_pipeline")
def run_training_pipeline(env: str = "local", pipeline_name: str = "training"):
    """Prefect task to run the Kedro training pipeline."""
    # Extract package name from pyproject.toml
    with open(project_root / "pyproject.toml", "rb") as f:
        package_name = tomllib.load(f)["tool"]["kedro"]["package_name"]

    configure_project(package_name)
    bootstrap_project(project_root)

    with KedroSession.create(project_path=project_root, env=env) as session:
        session.run(pipeline_name=pipeline_name)
```

### Add this to the flow
```python
@flow(name="training_flow", log_prints=True)
def training_flow(config_data_manager: dict[str, Any]):
    retraining_trigger_df = load_retraining_trigger_data(config_data_manager)
    run_training_pipeline(env="local", pipeline_name="training")
```

### Run the script

### We see that the pipeline is run but we don't see the logs, let's add it

### Add logger
```python
from prefect import flow, task, get_run_logger

@task(name="run_training_pipeline")
def run_training_pipeline(env: str = "local", pipeline_name: str = "training"):
    """Prefect task to run the Kedro training pipeline."""
    logger = get_run_logger()
    logger.info(f"Running training pipeline")
    # Extract package name from pyproject.toml
    with open(project_root / "pyproject.toml", "rb") as f:
        package_name = tomllib.load(f)["tool"]["kedro"]["package_name"]

    configure_project(package_name)
    bootstrap_project(project_root)

    with KedroSession.create(project_path=project_root, env=env) as session:
        session.run(pipeline_name=pipeline_name)
    
    logger.info(f"Training pipeline completed")

```

### Now, define the training and re-training logic
If we haven't run the monitoring pipeline, this might be empty.

That's also similar to when we run the pipeline first time

In this case, we run training.

Also, we need to run if the latest value of re-training is 1 AND we have not used it yet to train

Otherwise, we don't train it.

### First, we need to get the latest training timestamp from MLflow
```python
def get_last_training_timestamp() -> datetime | None:
    """Get timestamp of the most recently updated model (champion or challenger)."""
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:8080"))
    
    client = MlflowClient()
    model_name = config_mlflow["registered_model_name"]
    
    timestamps = []
    
    # Check champion
    try:
        champion_alias = config_mlflow["model_aliases"]["production"]  # "champion"
        model_version = client.get_model_version_by_alias(name=model_name, alias=champion_alias)
        if model_version.last_updated_timestamp is not None:
            timestamps.append(model_version.last_updated_timestamp)
    except Exception:
        pass  # No champion exists
    
    # Check challenger
    try:
        challenger_alias = config_mlflow["model_aliases"]["candidate"]  # "challenger"
        model_version = client.get_model_version_by_alias(name=model_name, alias=challenger_alias)
        if model_version.last_updated_timestamp is not None:
            timestamps.append(model_version.last_updated_timestamp)
    except Exception:
        pass  # No challenger exists
    
    if not timestamps:
        return None
    latest_timestamp = max(timestamps)
    return datetime.fromtimestamp(latest_timestamp / 1000.0)
```

### Then, we need to implement the re-train logic:
```python
@task
def should_retrain(retraining_trigger_df: pd.DataFrame) -> bool:
    """
    Check if the retraining trigger df is empty.
    """
    logger = get_run_logger()

    # Case 1: No previous training runs found in MLflow → run initial training
    last_training_timestamp = get_last_training_timestamp()
    if last_training_timestamp is None:
        logger.info(f"No previous training runs found - running initial training")
        return True

    # Case 2: Empty re-train table → first run, train model
    if retraining_trigger_df.empty:
        logger.info(f"No retraining triggers found - running initial training")
        return True

    # Get the LATEST row (last one after chronological ordering)
    trigger_row = retraining_trigger_df.iloc[-1]
    trigger_value = int(trigger_row["retraining_trigger"])
    trigger_timestamp = pd.to_datetime(trigger_row["Timestamps"])

    # Case 3: No drift detected in the last trigger → don't train
    if trigger_value == 0:
        logger.info(f"No data drift detected - skipping training")
        return False
    
    if trigger_value == 1:
        if trigger_timestamp > last_training_timestamp:
            logger.info(f"Data drift detected - running training")
            return True
        else:
            logger.info(f"Trigger timestamp is older than last training timestamp - skipping training")
            return False
        
    logger.info("No retraining triggers found - skipping training")
    return False
```

### Then update the flow:
```python
@flow(name="training_flow", log_prints=True)
def training_flow(config_data_manager: dict[str, Any]):
    logger = get_run_logger()
    logger.info(f"Starting training flow")
    retraining_trigger_df = load_retraining_trigger_data(config_data_manager)
    retrain_flag = should_retrain(retraining_trigger_df)
    if retrain_flag:
        logger.info(f"Retraining flag is True - running training pipeline")
        run_training_pipeline(env="local", pipeline_name="training")
    else:
        logger.info(f"Retraining flag is False - skipping training pipeline")
        pass
if __name__ == "__main__":
    training_flow(config_data_manager=config_data_manager)
```

### The schedule we will define later when we serve (aka deply) the flow

# Monitoring flow

### Create `src/prefect_orchestrator/monitoring_flow.py`

### Add a task
```python
import os
import tomllib
from pathlib import Path

from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from prefect import flow, task, get_run_logger

project_root = Path(__file__).resolve().parents[2]
os.chdir(project_root)


@task(name="run_monitoring_pipeline", log_prints=True)
def run_monitoring_pipeline(env: str = "local", pipeline_name: str = "monitoring"):
    """Prefect task to run the Kedro monitoring pipeline."""
    logger = get_run_logger()
    logger.info(f"Running monitoring pipeline")
    # Extract package name from pyproject.toml
    with open(project_root / "pyproject.toml", "rb") as f:
        package_name = tomllib.load(f)["tool"]["kedro"]["package_name"]

    configure_project(package_name)
    bootstrap_project(project_root)

    with KedroSession.create(project_path=project_root, env=env) as session:
        session.run(pipeline_name=pipeline_name)
    
    logger.info(f"Monitoring pipeline completed")
```

### Add a flow
```python
@flow(name="monitoring_flow", log_prints=True)
def monitoring_flow():
    logger = get_run_logger()
    logger.info(f"Starting monitoring flow")
    run_monitoring_pipeline()


if __name__ == "__main__":
    monitoring_flow()
```

### Run the script

# Inference flow
### Create the file `src/prefect_orchestrator/inference_flow.py`

### Add the inference flow run

### First, we need to check if there is new data
```python
import os
import sys
import tomllib
from pathlib import Path

from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from prefect import flow, task, get_run_logger

# Add src directory to path before imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))
sys.path.append(str(project_root))

# Change to project directory so relative paths resolve correctly
os.chdir(project_root)

from app_data_manager.data_manager import DataManager  # noqa: E402
from app_data_manager.utils import read_config  # noqa: E402

# Read configuration
parameters_path = project_root / "conf" / "base" / "parameters.yml"
config = read_config(parameters_path)

# Track last processed timestamp across flow runs
last_timestamp: str | None = None


@task(name="check_new_data", log_prints=True)
def check_new_data() -> tuple[bool, str | None]:
    """
    Check if new data is available by comparing timestamps.
    Returns (has_new_data, latest_timestamp).
    """
    global last_timestamp  # noqa: PLW0602, PLW0603
    logger = get_run_logger()
    data_manager = DataManager(config["data_manager"])
    
    df = data_manager.get_last_n_points(1, table_name="raw_data")
    latest_timestamp = df.iloc[-1]["Timestamps"]

    if last_timestamp is None or latest_timestamp > last_timestamp:
        logger.info(f"New data found: {latest_timestamp}")
        return True, latest_timestamp
    
    logger.info(f"No new data (last: {last_timestamp})")
    return False, None
```

### Then pipeline running node
```python
@task(name="run_inference_pipeline", log_prints=True)
def run_inference_pipeline(env: str = "local") -> None:
    """Run the Kedro inference pipeline programmatically."""
    logger = get_run_logger()
    logger.info("Running inference pipeline")
    with open(project_root / "pyproject.toml", "rb") as f:
        package_name = tomllib.load(f)["tool"]["kedro"]["package_name"]

    configure_project(package_name)
    bootstrap_project(project_root)

    with KedroSession.create(project_path=project_root, env=env) as session:
        session.run(pipeline_name="inference")
    
    logger.info("Inference pipeline completed")
```

### Then, add the flow
```python
@flow(name="inference_flow", log_prints=True)
def inference_flow(env: str = "local") -> None:
    """
    Check for new data and run inference pipeline if new data is available.
    Scheduling is handled by Prefect's serve with interval.
    """
    global last_timestamp  # noqa: PLW0602, PLW0603
    logger = get_run_logger()
    logger.info("Starting inference flow")
    
    has_new_data, latest_timestamp = check_new_data()

    if has_new_data:
        run_inference_pipeline(env=env)
        last_timestamp = latest_timestamp
        logger.info("Inference completed")
    else:
        logger.info("Skipping inference - no new data")


if __name__ == "__main__":
    inference_flow()

```

# Training deployment 
### Now, we need to create deployments.

### Show `Prefect Deployments` slide

### Now, let's add this as entrypoints

### Create folder `entrypoints/prefect`

### Create `entrypoints/prefect/training.py
```python
import os
import sys
from pathlib import Path
from datetime import timedelta
from prefect_orchestrator.training_flow import training_flow
from app_data_manager.utils import read_config

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))
sys.path.append(str(project_root))
os.chdir(project_root)

from app_data_manager.utils import read_config  # noqa: E402, type: ignore


# Read configuration
parameters_path = project_root / "conf" / "base" / "parameters.yml"
config = read_config(parameters_path)

# Read environment variables
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5001")
PREFECT_API_URL = os.getenv("PREFECT_API_URL", "http://127.0.0.1:4200/api")


if __name__ == "__main__":
    # Define how often to check for data drift
    check_frequency_minutes = config["training_pipeline"]["train_check_frequency"]
    config_data_manager = config["data_manager"]

    training_flow.serve(
        name="training-flow",
        interval=timedelta(minutes=check_frequency_minutes),
        parameters={"config_data_manager": config_data_manager},
    )
````

### Add `train_check_frequency` to the config:
```yaml
training_pipeline:
  start_timestamp: '2007-07-29 03:10:00'
  test_fraction: 0.2 # 20% of the data for testing
  n_folds: 3
  train_check_frequency: 1
```

### Run the script, show the run in the UI

# Monitoring deployment 
### Create `entrypoints/prefect/monitoring.py`

```python
import os
import sys
from pathlib import Path
from datetime import timedelta
from prefect_orchestrator.monitoring_flow import monitoring_flow
from app_data_manager.utils import read_config

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))
sys.path.append(str(project_root))
os.chdir(project_root)

from app_data_manager.utils import read_config  # noqa: E402, type: ignore


# Read configuration
parameters_path = project_root / "conf" / "base" / "parameters.yml"
config = read_config(parameters_path)

# Read environment variables
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5001")
PREFECT_API_URL = os.getenv("PREFECT_API_URL", "http://127.0.0.1:4200/api")


if __name__ == "__main__":
    # Define how often to check for data drift
    monitoring_frequency_minutes = config["monitoring_pipeline"]["monitoring_frequency"]

    monitoring_flow.serve(
        name="monitoring-flow",
        interval=timedelta(minutes=monitoring_frequency_minutes)
    )
```

### Add `monitoring_freq` to the config
```yaml
monitoring_pipeline:
  monitored_feature: "GenRPM"
  wasserstein_threshold: 10
  monitoring_frequency: 1
```

### Run the deployment

# Inference deployment 
### Create `entrypoints/prefect/inference.py`
```python
import os
import sys
from pathlib import Path
from datetime import timedelta
from prefect_orchestrator.inference_flow import inference_flow
from app_data_manager.utils import read_config

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))
sys.path.append(str(project_root))
os.chdir(project_root)

from app_data_manager.utils import read_config  # noqa: E402, type: ignore


# Read configuration
parameters_path = project_root / "conf" / "base" / "parameters.yml"
config = read_config(parameters_path)

# Read environment variables
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5001")
PREFECT_API_URL = os.getenv("PREFECT_API_URL", "http://127.0.0.1:4200/api")


if __name__ == "__main__":
    # Define how often to run inference (in seconds from config)
    inference_frequency_seconds = config["inference_pipeline"]["inference_frequency"]

    inference_flow.serve(
        name="inference-flow",
        interval=timedelta(seconds=inference_frequency_seconds)
    )
```