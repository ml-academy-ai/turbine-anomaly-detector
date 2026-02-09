from kedro.pipeline import Pipeline, node
from .nodes import load_champion_model, predict, save_predictions_to_db, compute_model_errors, smooth_error, detect_anomaly


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
            func=compute_model_errors,
            inputs=["predictions", "target_data"],
            outputs="model_errors",
        ),
        node(
            func=smooth_error,
            inputs=["model_errors", "params:inference_pipeline.smoothing_window"],
            outputs="smoothed_errors",
        ),
        node(
            func=detect_anomaly,
            inputs=["smoothed_errors", "params:inference_pipeline.anomaly_threshold"],
            outputs="anomalies",
        ),
        # node(
        #     func=save_predictions_to_db,
        #     inputs=[
        #         "predictions", 
        #         "params:inference_pipeline.predictions_column_name",
        #         "params:data_manager.predictions_table_name",
        #         "data_timestamps",
        #         "params:data_manager"
        #         ],
        #     outputs=None,
        # ),
        # node(
        #     func=save_predictions_to_db,
        #     inputs=[
        #         "predictions", 
        #         "params:inference_pipeline.errors_column_name",
        #         "params:data_manager.errors_table_name",
        #         "data_timestamps",
        #         "params:data_manager"
        #         ],
        #     outputs=None,
        # ),
    ])
