from kedro.pipeline import Pipeline, node
from .nodes import load_champion_model, predict, save_predictions_to_db


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
        node(
            func=save_predictions_to_db,
            inputs=["predictions", "data_timestamps", "params:data_manager"],
            outputs=None,
        ),
    ])
