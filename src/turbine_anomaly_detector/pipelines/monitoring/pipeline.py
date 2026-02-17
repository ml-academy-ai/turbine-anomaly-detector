from kedro.pipeline import Pipeline, node

from turbine_anomaly_detector.pipelines.feature_eng.nodes import (
    load_inference_batch,
    load_training_data_from_db,
)

from .nodes import get_retraining_trigger, get_wasserstein_distance_1d


def create_monitoring_pipeline():
    return Pipeline(
        [
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
                    "params:data_manager",
                ],
                outputs="monitored_data",
            ),
            node(
                func=get_wasserstein_distance_1d,
                inputs=[
                    "reference_data",
                    "monitored_data",
                    "params:monitoring_pipeline.monitored_feature",
                ],
                outputs="wasserstein_distance",
            ),
            node(
                func=get_retraining_trigger,
                inputs=[
                    "wasserstein_distance",
                    "params:monitoring_pipeline.wasserstein_threshold",
                ],
                outputs="retraining_trigger",
            ),
        ]
    )
