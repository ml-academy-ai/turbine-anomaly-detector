from kedro.pipeline import Pipeline, node
from .nodes import rename_columns

def create_pipeline() -> Pipeline:
    return Pipeline([
        node(
            func=rename_columns,
            inputs=["df_train", "params:feature_eng_pipeline.rename_columns"],
            outputs="renamed_data",
        )
    ])