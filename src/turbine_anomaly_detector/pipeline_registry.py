from kedro.pipeline import Pipeline

from turbine_anomaly_detector.pipelines.feature_eng.pipeline import (
    feat_eng_pipeline_inference,
    feat_eng_pipeline_training,
)
from turbine_anomaly_detector.pipelines.inference.pipeline import (
    create_pipeline as create_inference_pipeline,
)
from turbine_anomaly_detector.pipelines.monitoring.pipeline import (
    create_monitoring_pipeline,
)
from turbine_anomaly_detector.pipelines.training.pipeline import (
    create_pipeline as create_training_pipeline,
)


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
