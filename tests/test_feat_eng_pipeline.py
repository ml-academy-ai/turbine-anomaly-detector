"""Unit tests for feature_eng pipeline nodes."""
import pytest
import pandas as pd

from turbine_anomaly_detector.pipelines.feature_eng.nodes import add_lag_features, remove_diff_outliers


def test_add_lag_features_creates_expected_columns(sample_df):
    result = add_lag_features(sample_df, lags_dict={"col1": [1, 2], "col2": [1]})
    assert "col1_lag1" in result.columns
    assert "col1_lag2" in result.columns
    assert "col2_lag1" in result.columns
    assert result["col1_lag1"].iloc[1] == 10
    assert result["col1_lag2"].iloc[2] == 10
    assert result["col2_lag1"].iloc[1] == 1


def test_remove_diff_outliers_one_column(dataset_with_outliers):
    result = remove_diff_outliers(
        dataset_with_outliers,
        diff_thresholds={"power": 30},
    )
    assert result.notna().all().all() # make sure no NaN values are introduced
    assert result["power"].iloc[5] != 200 # make sure the outlier is removed
    assert result["power"].iloc[10] != -10 # make sure the outlier is removed