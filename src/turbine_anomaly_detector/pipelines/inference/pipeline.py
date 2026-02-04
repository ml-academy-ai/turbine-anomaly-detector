from kedro.pipeline import Pipeline, node
from .nodes import load_champion_model, predict


def create_pipeline(**kwargs) -> Pipeline:
    """Create the inference pipeline."""
    return Pipeline([
        node(
            func=load_champion_model,
            inputs=["params:mlflow"],
            outputs="champion_model",
        ),
        node(
            func=predict,
            inputs=["features_data", "champion_model"],
            outputs="predictions",
        ),
    ])
