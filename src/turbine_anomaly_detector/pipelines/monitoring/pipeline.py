"""Monitoring pipeline."""
from kedro.pipeline import Pipeline, node
from .nodes import compute_anomaly_metrics


def create_pipeline(**kwargs) -> Pipeline:
    """Create the monitoring pipeline."""
    return Pipeline([
        node(
            func=compute_anomaly_metrics,
            inputs=["predictions", "target_data"],
            outputs="anomaly_metrics",
        ),
    ])
