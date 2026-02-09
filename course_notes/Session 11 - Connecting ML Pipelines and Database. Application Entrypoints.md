# Connecting Database to ML Pipelines
### Show the slide how we will build different inputs for `Training` and `Inference` Pipelines
### Implement data reading node
```python
from app_data_manager.data_manager import DataManager

def load_training_data_from_db(
    start_timestamp: str,
    table_name: str,
    data_manager_config: dict[str, Any],
) -> pd.DataFrame:
    """
    Load training data from SQLite database by timestamp range.

    Args:
        start_timestamp: Start timestamp (inclusive)
        end_timestamp: End timestamp (inclusive)
        table_name: Name of the table to read from
        data_manager_config: DataManager configuration dictionary

    Returns:
        DataFrame containing data within the timestamp range
    """
    data_manager = DataManager(data_manager_config)

    df = data_manager.get_data_since_timestamp(
        start_timestamp=start_timestamp,
        table_name=table_name,
    )

    return df
```

### Add the starting timestamp to the `training pipleine` config
```yaml
training_pipeline:
  start_timestamp: '2007-07-29 03:10:00'
  test_fraction: 0.2 # 20% of the data for testing
  n_folds: 3
```

### Add function that creates a pipeline
```yaml
def load_training_data(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=load_training_data_from_db,
                inputs=[
                    "params:training_pipeline.start_timestamp",
                    "params:data_manager.raw_data_table_name",
                    "params:data_manager",
                ],
                outputs="loaded_df",
            ),
        ]
    )
```

### Concatenate pipelines
```python
def feat_eng_pipeline_training(**kwargs) -> Pipeline:
    return load_training_data + create_pipeline()
```

### Change `train_df` to `loaded_df` in `create_pipeline` function

### Add the pipeline to the pipeline registry
```python
from turbine_anomaly_detector.pipelines.feature_eng.pipeline import feat_eng_pipeline_training

def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    feature_eng_pipeline_train = feat_eng_pipeline_training()
    training_pipeline = create_training_pipeline()
    inference_pipeline = create_inference_pipeline()

    return {
        "__default__": feature_eng_pipeline_train + training_pipeline,
        "training": feature_eng_pipeline_train + training_pipeline,
        # "inference": feature_eng_pipeline + inference_pipeline,
    }
```
### Run training pipeline

### Add data reading for the inference
```python
def get_inference_batch(
    batch_size: int,
    table_name: str,
    data_manager_config: dict[str, Any],
) -> pd.DataFrame:
    """
    Get the last N data points from SQLite database.

    Args:
        batch_size: Number of points to retrieve
        table_name: Name of the table to read from
        data_manager_config: DataManager configuration dictionary

    Returns:
        DataFrame containing the last N rows, ordered by Timestamps
    """
    data_manager = DataManager(data_manager_config)
    df = data_manager.get_last_n_points(n=batch_size, table_name=table_name)
    return df
```

### Create New Loading Pipeline for Inference
```python
def load_inference_data(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=load_inference_batch,
                inputs=[
                    "params:inference_pipeline.batch_size", 
                    "params:data_manager.raw_data_table_name", 
                    "params:data_manager"],
                outputs="loaded_df",
            ),
        ]
        )
```

### Add `batch_size` to the config file
```yaml
inference_pipeline:
  batch_size: 100
```

### Concatenate pipelines for inference
```python
def feat_eng_pipeline_inference() -> Pipeline:
    return load_inference_data() + create_pipeline()
```

### Add Pipeline to the Pipeline Registry
```python
from kedro.pipeline import Pipeline
from turbine_anomaly_detector.pipelines.feature_eng.pipeline import feat_eng_pipeline_training, feat_eng_pipeline_inference
from turbine_anomaly_detector.pipelines.training.pipeline import create_pipeline as create_training_pipeline
from turbine_anomaly_detector.pipelines.inference.pipeline import create_pipeline as create_inference_pipeline

def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    feature_eng_pipeline_train = feat_eng_pipeline_training()
    feature_eng_pipeline_inference = feat_eng_pipeline_inference()
    training_pipeline = create_training_pipeline()
    inference_pipeline = create_inference_pipeline()

    return {
        "__default__": feature_eng_pipeline_train + training_pipeline,
        "training": feature_eng_pipeline_train + training_pipeline,
        "inference": feature_eng_pipeline_inference + inference_pipeline,
    }
```
``
### We need to save our predictions. Let's implement the node for this
```python
from app_data_manager.data_manager import DataManager
def save_predictions_to_db(
    y_pred: pd.Series,
    predictions_column_name: str,
    db_table_name: str,
    data_timestamps: pd.Timestamp,
    data_manager_config: dict[str, Any],
) -> None:
    """
    Save predictions to the SQLite database using DataManager.

    Args:
        y_pred: Predicted values as a Series
        column_name: Name of the column to save the predictions to
        db_table_name: Name of the table to save the predictions to
        data_timestamps: Data timestamps
        data_manager_config: DataManager configuration dictionary
    """
    # Initialize DataManager
    data_manager = DataManager(data_manager_config)
    # Convert input timestamps to pandas datetime
    timestamps = pd.to_datetime(data_timestamps["Timestamps"])

    # Normalize timestamps to string format expected by the database
    # This works for both Series-like inputs and single Timestamp values
    timestamps_str = timestamps.dt.strftime("%Y-%m-%d %H:%M:%S")

    # Create predictions DataFrame
    predictions_df = pd.DataFrame(
        {
            "Timestamps": timestamps_str,
            predictions_column_name: y_pred.values.ravel(),
        }
    )
    # Save to predictions table
    data_manager.insert_data_to_db(
        new_data=predictions_df,
        table_name=db_table_name
    )
```

### Add get_data_timestamps to `feat_eng_pipeline`

```python
def get_data_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get the current timestamp from the dataframe.
    """
    return pd.DataFrame(df["Timestamps"].values, columns=["Timestamps"])
```

### Add the node after column renaming
```python
node(
    func=rename_columns,
    inputs=[
        "loaded_df",
        "params:feature_eng_pipeline.rename_columns",
    ],
    outputs="renamed_data",
),
node(
    func=get_data_timestamps,
    inputs="renamed_data",
    outputs="data_timestamps",
),
```

### Add new parameters of the prediction names
```yaml
inference_pipeline:
  batch_size: 100
  smoothing_window: 5
  anomaly_threshold: 9.5 # in percentage
  predictions_column_name: predict_power
  anomalies_column_name: anomaly
  errors_column_name: mape
```

### Show the slides how we will save `predictions`, `errors` and `anomalies` to different database tables
### Add `save_predictions_to_db` node to the pipeline
```python
node(
    func=save_predictions_to_db,
    inputs=[
        "predictions", 
        "params:inference_pipeline.predictions_column_name",
        "params:data_manager.predictions_table_name",
        "data_timestamps",
        "params:data_manager"
        ],
    outputs=None,
),
```

### Check if predictions are there
- Make sure the predictions table exist by running the uncommented script, then inference
- Then run
```python
import os
import sys
from pathlib import Path

import pandas as pd
from data_manager import DataManager  # type: ignore
from utils import read_config  # type: ignore

# Add project root and app_ui directory to path
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))
os.chdir(project_root)


if __name__ == "__main__":
    config = read_config(os.path.join(project_root, "conf", "base", "parameters.yml"))
    data_manager = DataManager(config["data_manager"])

    # data_manager.init_raw_db_table()
    # data = data_manager.get_last_n_points(10, table_name="raw_data")
    
    # inference_data = pd.read_parquet(
    #     os.path.join(project_root, "data", "01_raw", "df_prod.parquet")
    # )
    # data_manager.insert_data_to_db(inference_data, table_name="raw_data")

    # data_manager.init_predictions_db_table()

    # data = data_manager.get_data_since_timestamp(
    #     start_timestamp="2009-01-01 00:00:00", 
    #     table_name="raw_data"
    #     )
    data = data_manager.get_last_n_points(10, table_name="predictions")
    print(data)
```

### Saving Errors to the Database - add a new node
```python
node(
    func=save_predictions_to_db,
    inputs=[
        "model_errors", 
        "params:inference_pipeline.errors_column_name",
        "params:data_manager.errors_table_name",
        "data_timestamps",
        "params:data_manager"
        ],
    outputs=None,
),
```

### Init the `error_table`
```python
if __name__ == "__main__":
    config = read_config(os.path.join(project_root, "conf", "base", "parameters.yml"))
    data_manager = DataManager(config["data_manager"])

    # data_manager.init_raw_db_table()
    # data = data_manager.get_last_n_points(10, table_name="raw_data")
    # # print(data)
    
    # inference_data = pd.read_parquet(
    #     os.path.join(project_root, "data", "01_raw", "df_prod.parquet")
    # )
    # data_manager.insert_data_to_db(inference_data, table_name="raw_data")
    # data_manager.init_predictions_db_table()
    # data = data_manager.get_data_since_timestamp(
    #     start_timestamp="2009-01-01 00:00:00", 
    #     table_name="raw_data"
    #     )
    # data = data_manager.get_last_n_points(10, table_name="predictions")
    # print(data)
    data_manager.init_errors_db_table()
```

### Run inference again and check if errors in the table
```python
if __name__ == "__main__":
    config = read_config(os.path.join(project_root, "conf", "base", "parameters.yml"))
    data_manager = DataManager(config["data_manager"])

    # data_manager.init_raw_db_table()
    # data = data_manager.get_last_n_points(10, table_name="raw_data")
    # # print(data)
    
    # inference_data = pd.read_parquet(
    #     os.path.join(project_root, "data", "01_raw", "df_prod.parquet")
    # )
    # data_manager.insert_data_to_db(inference_data, table_name="raw_data")
    # data_manager.init_predictions_db_table()
    # data = data_manager.get_data_since_timestamp(
    #     start_timestamp="2009-01-01 00:00:00", 
    #     table_name="raw_data"
    #     )
    # data = data_manager.get_last_n_points(10, table_name="predictions")
    # print(data)
    data_manager.init_errors_db_table()
    data = data_manager.get_last_n_points(10, table_name="errors")
    print(data)
```

### Add saving anomaly
```python
node(
    func=save_predictions_to_db,
    inputs=[
        "anomalies", 
        "params:inference_pipeline.anomalies_column_name",
        "params:data_manager.anomalies_table_name",
        "data_timestamps",
        "params:data_manager"
        ],
    outputs=None,
),
```

### Create anomaly table first
```python
data_manager.init_anomalies_db_table()
```

### Run inference again
### Run reading anomalies
```python
data = data_manager.get_last_n_points(10, table_name="anomalies")
print(data)
```

# Application Entrypoints
### Show Intro Slide about Entrypoints
### Adding Training Entrypoint
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

### Adding Inference Entrypoint
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