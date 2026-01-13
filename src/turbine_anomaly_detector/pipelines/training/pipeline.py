from kedro.pipeline import Pipeline, node
from .nodes import train_test_split, tune_hyperparameters


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline([
        node(
            func=train_test_split,
            inputs=["features_data", "target_data", "params:training_pipeline"],
            outputs=["x_train", "y_train", "x_test", "y_test"],
        ),
        node(
            func=tune_hyperparameters,
            inputs=["x_train", "y_train", "params:training_pipeline"],
            outputs="tuning_results"
            ),
    ])