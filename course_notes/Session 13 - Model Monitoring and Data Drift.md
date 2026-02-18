# Model Monitoring Intro
### Introduce Data Drift and Concept Drift
### Introduce Approach to Monitoring and Re-training in the Project including Monitoring and Re-training Logic Slide
### Go through `06 - Model Monitoring Notebook`

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

### Add this node to the pipeline:
```python
def get_retraining_trigger(
    wasserstein_distance: float,
    threshold: float,
) -> int:
    """
    Determine if retraining is needed based on Wasserstein distance.
    """
    if wasserstein_distance > threshold:
        return 1
    else:
        return 0
```

### Add threshold to the config file:
```yaml
monitoring_pipeline:
  monitored_feature: "GenRPM"
  wasserstein_threshold: 315
```

### We will use this trigger to re-train the pipeline when we introduce orchestration