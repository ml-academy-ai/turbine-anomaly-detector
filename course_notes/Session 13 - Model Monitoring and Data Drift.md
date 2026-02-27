# Model Monitoring Intro
### Introduce Data Drift and Concept Drift
### Introduce Approach to Monitoring and Re-training in the Project including Monitoring and Re-training Logic Slide
### Go through `06 - Model Monitoring Notebook`

### We will implement the simplified version of re-training

### Create a Node in the Monitoring Pipeline Directory
```python
import numpy as np
import pandas as pd
from typing import Optional

def get_wasserstein_distance_1d(
    reference_df: pd.DataFrame,
    monitored_df: pd.DataFrame,
    feature_col: str,
    bins: Optional[int] = None,
) -> float:
    """
    Histogram-based approximation of 1D Wasserstein distance
    for a specific feature column.
    """

    reference = reference_df[feature_col].dropna().to_numpy()
    monitored = monitored_df[feature_col].dropna().to_numpy()

    full_dataset = np.concatenate((reference, monitored))

    if bins is None:
        _, bin_edges = np.histogram(full_dataset, bins="doane")
    else:
        bin_edges = np.linspace(
            min(reference.min(), monitored.min()),
            max(reference.max(), monitored.max()),
            bins + 1
        )

    ref_hist, _ = np.histogram(reference, bins=bin_edges)
    mon_hist, _ = np.histogram(monitored, bins=bin_edges)

    ref_p = ref_hist / ref_hist.sum()
    mon_p = mon_hist / mon_hist.sum()

    ref_cdf = np.cumsum(ref_p)
    mon_cdf = np.cumsum(mon_p)

    bin_widths = np.diff(bin_edges)

    return float(np.sum(np.abs(ref_cdf - mon_cdf) * bin_widths))
```

### Add this to the Config:
```yaml
monitoring_pipeline:
  monitored_feature: "GenRPM"
```

### Add Nodes to the `Monitoring Pipeline`
```python
from kedro.pipeline import Pipeline, node
from .nodes import get_wasserstein_distance_1d
from turbine_anomaly_detector.pipelines.feature_eng.nodes import load_training_data_from_db
from turbine_anomaly_detector.pipelines.feature_eng.nodes import load_inference_batch

def create_monitoring_pipeline():
    return Pipeline([
        node(
                func=load_training_data_from_db,
                inputs=[
                    "params:training_pipeline.start_timestamp",
                    "params:data_manager.raw_data_table_name",
                    "params:data_manager",
                ],
                outputs="reference_data",
            ),
        node(
            func=load_inference_batch,
            inputs=[
                "params:inference_pipeline.batch_size", 
                "params:data_manager.raw_data_table_name", 
                "params:data_manager"
                ],
            outputs="monitored_data",
        ),
        node(
            func=get_wasserstein_distance_1d,
            inputs=[
                "reference_data", 
                "monitored_data",
                "params:monitoring_pipeline.monitored_feature"
                ],
            outputs="wasserstein_distance",
        )
    ])
```

### Update Pipeline Registry:
```python
from kedro.pipeline import Pipeline
from turbine_anomaly_detector.pipelines.feature_eng.pipeline import feat_eng_pipeline_training, feat_eng_pipeline_inference
from turbine_anomaly_detector.pipelines.training.pipeline import create_pipeline as create_training_pipeline
from turbine_anomaly_detector.pipelines.inference.pipeline import create_pipeline as create_inference_pipeline
from turbine_anomaly_detector.pipelines.monitoring.pipeline import create_monitoring_pipeline

def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    feature_eng_pipeline_train = feat_eng_pipeline_training()
    feature_eng_pipeline_inference = feat_eng_pipeline_inference()
    training_pipeline = create_training_pipeline()
    inference_pipeline = create_inference_pipeline()
    monitoring_pipeline = create_monitoring_pipeline()
    return {
        "__default__": feature_eng_pipeline_train + training_pipeline,
        "training": feature_eng_pipeline_train + training_pipeline,
        "inference": feature_eng_pipeline_inference + inference_pipeline,
        "monitoring": monitoring_pipeline,
    }
```

### Create a re-training trigger node:
```python
def get_retraining_trigger(
    wasserstein_distance: float,
    threshold: float,
    monitored_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Determine if retraining is needed based on Wasserstein distance.
    """
    last_timestamp = monitored_data["Timestamps"].iloc[-1]
    if wasserstein_distance > threshold:
        retraining_trigger = 1
    else:
        retraining_trigger = 0
    # Create a DataFrame with the retraining trigger information
    retraining_trigger_df = pd.DataFrame(
        {
            "Timestamps": [last_timestamp],
            "wasserstein_distance": [wasserstein_distance],
            "retraining_trigger": [retraining_trigger],
        }
    )
    return retraining_trigger_df
```

### Add the node to the pipeline
```python
node(
    func=get_retraining_trigger,
    inputs=[
        "wasserstein_distance",
        "params:monitoring_pipeline.wasserstein_threshold",
        "monitored_data",
    ],
    outputs="retraining_trigger_df",
),
```

### Add threshold to the config file:
```yaml
monitoring_pipeline:
  monitored_feature: "GenRPM"
  wasserstein_threshold: 315
```

### Now, we need to store this in the database.

### Let's create a table for storing this data
```yaml
retraining_trigger_table_schema:
    - name: Timestamps
      type: TEXT
      primary_key: true
      not_null: true
    - name: wasserstein_distance
      type: REAL
      not_null: true
    - name: retraining_trigger
      type: INTEGER
      not_null: true
```

### Add a new table name to the data manager config
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
  retraining_trigger_table_name: retraining_trigger # <-------
```

### Create a method to initialize this table
```python
def init_retraining_trigger_db_table(self) -> None:
        """
        Create retraining trigger table and timestamp index if they don't exist.
        """
        Path(self.config["sqlite_db_path"]).parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            schema_sql = self._build_schema_sql(self.config["retraining_trigger_table_schema"])
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self.config['retraining_trigger_table_name']} ({schema_sql})"
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_timestamps "
                f"ON {self.config['retraining_trigger_table_name']} (Timestamps)"
            )
```

### Create a node to save the trigger to the database
```python
def save_retraining_trigger_to_db(
    retraining_trigger_df: pd.DataFrame,
    data_manager_config: dict[str, Any],
    db_table_name: str,
) -> None:
    """
    Save the retraining trigger information to the database.
    """
    # Initialize DataManager
    data_manager = DataManager(data_manager_config)
    # Save to retraining trigger table
    data_manager.insert_data_to_db(new_data=retraining_trigger_df, table_name=db_table_name)
```

###  Add node to the Pipeline
```python
node(
    func=save_retraining_trigger_to_db,
    inputs=[
        "retraining_trigger_df",
        "params:data_manager",
        "params:data_manager.retraining_trigger_table_name",
    ],
    outputs=None,
),
```

### We need to initialize the re-training trigger in the database.
- We can do that by adding init_table call in the data app entrypoint.
- Go to `entrypoints/app_stread_data`
- Add:
```python
while True:
    # Clean database by reinitializing the raw data table
    data_manager.init_raw_db_table()
    # Initialize other tables
    data_manager.init_predictions_db_table()
    data_manager.init_errors_db_table()
    data_manager.init_anomalies_db_table()
    data_manager.init_retraining_trigger_db_table()
```

### Run the script
```bash
python `entrypoints/app_stream_data.py`
```

### Run Kedro pipeline
```bash
kedro run --pipeline=monitoring
```

### We will use this trigger to re-train the pipeline when we introduce orchestration