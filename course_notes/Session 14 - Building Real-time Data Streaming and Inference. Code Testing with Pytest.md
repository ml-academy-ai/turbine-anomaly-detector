# Data Streaming App
### Explain the slide `Real-time data ingestion`
### Create `entrypoints/app_stream_data.py`
```python
import os
import time
from pathlib import Path
import pandas as pd
from app_data_manager.data_manager import DataManager
from app_data_manager.utils import read_config

project_root = Path(__file__).resolve().parents[1]
os.chdir(project_root)

def stream_data_to_db() -> None:
    """
    Stream data point-by-point to the database with a delay between each insertion.
    Uses streaming_frequency and raw_data_table_name from config (data_manager section).
    """
    config = read_config(os.path.join(project_root, "conf", "base", "parameters.yml"))
    config_data_manager = config["data_manager"]
    data_manager = DataManager(config_data_manager)

    # Load inference data from config
    inference_data_folder = config_data_manager["inference_data_folder"]
    inference_data_filename = config_data_manager["inference_data_filename"]
    data_path = os.path.join(
        project_root, inference_data_folder, inference_data_filename
    )
    inference_data = pd.read_parquet(data_path)

    while True:
        # Clean database by reinitializing the raw data table
        data_manager.init_raw_db_table()
        # Initialize other tables
        data_manager.init_predictions_db_table()
        data_manager.init_errors_db_table()
        data_manager.init_anomalies_db_table()

        # Iterate over each row and insert one at a time
        for idx, row in inference_data.iterrows():
            # Convert single row to DataFrame for insertion
            row_df = row.to_frame().T

            # Insert single row
            data_manager.insert_data_to_db(row_df, table_name=config_data_manager["raw_data_table_name"])

            # Sleep before next insertion
            if idx < len(inference_data) - 1:  # Don't sleep after last row
                time.sleep(config_data_manager["streaming_frequency"])

            print(idx)
            # print(data.iloc[-1])
if __name__ == "__main__":
    stream_data_to_db()
```

### Add `streaming_frequency` to the config file:
```yaml
data_manager:
  history_data_folder: data/01_raw
  history_data_filename: df_train_test.parquet
  inference_data_folder: data/01_raw
  inference_data_filename: df_prod.parquet
  sqlite_db_path: data/sqlite/app.db
  raw_data_table_name: raw_data
  predictions_table_name: predictions
  errors_table_name: errors
  anomalies_table_name: anomalies
  streaming_frequency: 2
```

### Run `entrypoints/app_stream_data.py`

# Real-time inference
### Explain the slide `Data flow in inference`

### Add `inference_frequency` to the config file:
```yaml
inference_pipeline:
  batch_size: 100
  rolling_window: 5
  anomaly_error_type: mape
  anomaly_threshold: 9.5 # in percentage
  inference_frequency: 2  # seconds between checks for new data
  predictions_column_name: [predict_power]
  anomalies_column_name: [anomaly]
  errors_column_names: [mape, rolling_mape]
```

### Change `streaming_frequency` to 10:
```yaml
data_manager:
  history_data_folder: data/01_raw
  history_data_filename: df_train_test.parquet
  inference_data_folder: data/01_raw
  inference_data_filename: df_prod.parquet
  sqlite_db_path: data/sqlite/app.db
  raw_data_table_name: raw_data
  predictions_table_name: predictions
  errors_table_name: errors
  anomalies_table_name: anomalies
  streaming_frequency: 10
```

### Add `inference_real_time.py`
```python
import os
import sys
import time
import tomllib
from pathlib import Path

from kedro.framework.project import configure_project 
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

# Add src directory to path before imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))
sys.path.append(str(project_root))

# Change to project directory so relative paths resolve correctly
os.chdir(project_root)

from app_data_manager.data_manager import DataManager 
from app_data_manager.utils import read_config


def run_inference_pipeline(env: str = "local") -> None:
    """Run the Kedro inference pipeline programmatically."""
    with open(project_root / "pyproject.toml", "rb") as f:
        package_name = tomllib.load(f)["tool"]["kedro"]["package_name"]

    configure_project(package_name)
    bootstrap_project(project_root)

    with KedroSession.create(project_path=project_root, env=env) as session:
        session.run(pipeline_name="inference")


def run_inference_real_time(env: str = "local") -> None:
    """
    Continuously check for new data and run inference pipeline when new data is available.
    Configuration is read from parameters.yml (inference_pipeline section).
    """
    config = read_config(os.path.join(project_root, "conf", "base", "parameters.yml"))
    data_manager = DataManager(config["data_manager"])
    inference_frequency = config["inference_pipeline"]["inference_frequency"]
    last_timestamp: str | None = None

    while True:
        try:
            df = data_manager.get_last_n_points(1, table_name="raw_data")
            latest_timestamp = df.iloc[-1]["Timestamps"]

            if last_timestamp is None or latest_timestamp > last_timestamp:
                run_inference_pipeline(env=env)
                last_timestamp = latest_timestamp

            time.sleep(inference_frequency)
        except Exception as e:
            time.sleep(inference_frequency)
            raise e


if __name__ == "__main__":
    run_inference_real_time()
```

### Run the sequence:
- python entrypoints/app_ui.py
- python entrypoints/app_stream_data.py
- python entrypoints/inference_real_time.py

### Say this is ALREADY GOOD ENOUGH for production, many apps run like this

### Ideally, we need to take the last time step only in the pipeline, but for demonstration, it's better to have the batch and overwrite.

# Code Testing with Pytest
### Introduce Python testing up to `Unit Tests` example and say that we will use Pytest in the project
### Got to the `src/ test` directory, delete `test_run.py`, we don't need it.

### Add `pytest` to uv
```bash
uv add pytest
uv add pytest-cov
```

### Create `test_feat_eng_pipeline.py`
```python
"""Unit tests for feature_eng pipeline nodes."""
import pytest
import pandas as pd

from turbine_anomaly_detector.pipelines.feature_eng.nodes import add_lag_features


def test_add_lag_features_creates_expected_columns():
    df = pd.DataFrame({"col1": [10, 20, 30, 40], "col2": [1, 2, 3, 4]})
    result = add_lag_features(df, lags_dict={"col1": [1, 2], "col2": [1]})
    assert "col1_lag1" in result.columns
    assert "col1_lag2" in result.columns
    assert "col2_lag1" in result.columns
    assert result["col1_lag1"].iloc[1] == 10
    assert result["col1_lag2"].iloc[2] == 10
    assert result["col2_lag1"].iloc[1] == 1
```

### Run
```bash
pytest tests/test_feat_eng_pipeline.py                                     
```
### We see the test report
- We see which part of the code is tested or not
- We see the test coverage - how much of your source code is executed when the tests run.
- So, you can have a high vocerage but poor testing still, but it gives you some indication

### Let's break something
- E.g., change `assert result["col2_lag1"].iloc[1] == 1` to `==2`
- We see the test failed.

### We can also test everything in the folder
```bash
pytest tests
```

### However, for this, the file must start with `test_...`
### Also, the name of the functions must start with `test_....`

### To re-use different objects in different tests, we can use `conftest.py`
- This file is used to store different configurations for the test
- In the majority of cases, it's used to store fixtures
- Fixtures are reusable components across tests

### Add fixture to `conftest.py`
```python
import pytest
import pandas as pd


@pytest.fixture
def sample_df():
    return pd.DataFrame({"col1": [10, 20, 30, 40], "col2": [1, 2, 3, 4]})
```

### Then, we can use this fixture
```python
def test_add_lag_features_creates_expected_columns(sample_df):
    result = add_lag_features(sample_df, lags_dict={"col1": [1, 2], "col2": [1]})
    assert "col1_lag1" in result.columns
    assert "col1_lag2" in result.columns
    assert "col2_lag1" in result.columns
    assert result["col1_lag1"].iloc[1] == 10
    assert result["col1_lag2"].iloc[2] == 10
    assert result["col2_lag1"].iloc[1] == 1
```

### We can even run tests with CLI command `pytest`


### Add one more fixture + `import numpy as np`
```python
@pytest.fixture
def dataset_with_outliers():
    """Small synthetic dataset with outliers in one column only."""
    n = 15
    timestamps = pd.date_range("2024-01-01", periods=n, freq="h")
    # Smooth series
    t = np.linspace(0, 2 * np.pi, n)
    power = 50 + 10 * np.sin(t)

    df = pd.DataFrame({"power": power, "Timestamps": timestamps})

    # Outliers in power only
    df.loc[5, "power"] = 200   # spike
    df.loc[10, "power"] = -10  # impossible drop
    return df
```

### Add a test
```python
def test_remove_diff_outliers_one_column(dataset_with_outliers):
    result = remove_diff_outliers(
        dataset_with_outliers,
        diff_thresholds={"power": 30},
    )
    assert result.notna().all().all() # make sure no NaN values are introduced
    assert result["power"].iloc[5] != 200 # make sure the outlier is removed
    assert result["power"].iloc[10] != -10 # make sure the outlier is removed
```


### We stop here
“In most ML teams, the highest ROI comes from strong unit tests and clean pipeline design. 
Deep integration testing across services is typically handled by platform or DevOps teams.”