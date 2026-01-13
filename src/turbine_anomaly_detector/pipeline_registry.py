from kedro.pipeline import Pipeline
from turbine_anomaly_detector.pipelines.feature_eng.pipeline import create_pipeline as create_feature_eng_pipeline
from turbine_anomaly_detector.pipelines.training.pipeline import create_pipeline as create_training_pipeline

def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    feature_eng_pipeline = create_feature_eng_pipeline()
    training_pipeline = create_training_pipeline()

    return {
        "__default__": feature_eng_pipeline + training_pipeline
    }
