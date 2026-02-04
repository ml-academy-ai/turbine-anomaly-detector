"""Monitoring pipeline."""
from kedro.pipeline import Pipeline, node
from .nodes import compute_anomaly_metrics, smooth_metric


def create_pipeline(**kwargs) -> Pipeline:
    """Create the monitoring pipeline."""
    return Pipeline([
        node(
            func=compute_anomaly_metrics,
            inputs=["predictions", "target_data"],
            outputs="anomaly_metrics",
        ),
        node(
            func=smooth_metric,
            inputs=["anomaly_metrics", "params:monitoring_pipeline.smoothing_window"],
            outputs="smoothed_anomaly_metrics",
        ),
    ])
