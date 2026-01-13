from kedro.pipeline import Pipeline, node
from .nodes import rename_columns, drop_columns, remove_diff_outliers, smooth_signal, add_lag_features, add_rolling_features, get_features_and_target

def create_pipeline() -> Pipeline:
    return Pipeline([
        node(
            func=rename_columns,
            inputs=["df_train", "params:feature_eng_pipeline.rename_columns"],
            outputs="renamed_data",
        ),
        node(
            func=drop_columns,
            inputs=["renamed_data", "params:feature_eng_pipeline.drop_columns"],
            outputs="dropped_columns_data",
        ),
        node(
            func=remove_diff_outliers,
            inputs=["dropped_columns_data", "params:feature_eng_pipeline.diff_outliers_thresholds"],
            outputs="removed_outliers_data",
        ),
        node(
            func=smooth_signal,
            inputs=[
                "removed_outliers_data", 
                "params:feature_eng_pipeline.smooth_signal.columns", 
                "params:feature_eng_pipeline.smooth_signal.window", 
                "params:feature_eng_pipeline.smooth_signal.method"
            ],
            outputs="smoothed_data",
        ),
        node(
            func=add_lag_features,
            inputs=[
                "smoothed_data", 
                "params:feature_eng_pipeline.lag_features"
            ],
            outputs="lagged_data",
        ),
        node(
            func=add_rolling_features,
            inputs=[
                "lagged_data", 
                "params:feature_eng_pipeline.rolling_features"
            ],
            outputs="rolled_stats_data",
        ),
        node(
            func=get_features_and_target,
            inputs=[
                "rolled_stats_data", 
                "params:feature_eng_pipeline.target"
            ],
            outputs=["features_data", "target_data"],
        ),
    ])