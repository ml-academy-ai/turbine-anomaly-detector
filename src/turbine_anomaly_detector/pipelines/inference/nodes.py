from typing import Any

import numpy as np
import pandas as pd

from app_data_manager.data_manager import DataManager
from turbine_anomaly_detector.common.mlflow_utils import load_model_by_alias


def load_champion_model(mlflow_params: dict[str, Any]) -> Any:
    """
    Load the production (champion) model from MLflow model registry.

    Wrapper that extracts config values and calls load_model_by_alias.

    Parameters
    ----------
    mlflow_params : dict[str, Any]
        MLflow config containing 'registered_model_name' and 'model_aliases'.

    Returns
    -------
    Any
        The loaded production model (MLflow pyfunc model) with scaler bundled.
    """
    registered_model_name = mlflow_params["registered_model_name"]
    production_alias = mlflow_params["model_aliases"]["production"]
    return load_model_by_alias(registered_model_name, alias=production_alias)


def predict(features_data: pd.DataFrame, champion_model: Any) -> pd.DataFrame:
    """
    Make predictions using the champion model on new data.

    Parameters
    ----------
    features_data : pd.DataFrame
        Input features for prediction. Must have the same columns as the
        training data (excluding the target column).
    champion_model : Any
        Loaded champion model (MLflow pyfunc model) that has a `predict` method.

    Returns
    -------
    pd.Series
        Predicted target values for the input features.
    """
    predictions = champion_model.predict(features_data)
    return pd.DataFrame(predictions, columns=["predict_power"])


def compute_model_errors(
    y_pred: pd.Series, y_true: pd.Series, anomaly_error_type: str
) -> pd.DataFrame:
    """
    Compute MAPE metric from predictions and target data.

    Parameters
    ----------
    y_pred : pd.Series
        Predicted values.
    target_data : pd.Series
        Ground truth target values.

    Returns
    -------
    dict[str, float]
        Dictionary containing 'mae', 'rmse', and 'mape' metrics.
    """
    y_true = y_true.values.ravel()
    y_pred = y_pred.values.ravel()
    if anomaly_error_type == "mape":
        error = np.abs(y_true - y_pred) / (y_true + 1e-8) * 100
        error_column_name = "mape"
    return pd.DataFrame(error, columns=[error_column_name])


def compute_rolling_error(df_error: pd.DataFrame, rolling_window: int) -> pd.DataFrame:
    """
    Smooth a metric using a rolling window.
    """
    error_name = df_error.columns[0]
    df_error[f"rolling_{error_name}"] = (
        df_error[error_name].rolling(window=rolling_window).median().bfill()
    )
    return df_error


def detect_anomaly(
    df_error: pd.DataFrame, threshold: float, anomaly_error_type: str
) -> pd.DataFrame:
    """
    Detect anomalies using a threshold.
    """
    df_anomaly = pd.DataFrame(
        {"anomaly": (df_error[f"rolling_{anomaly_error_type}"] > threshold).astype(int)}
    )
    return df_anomaly


def save_predictions_to_db(
    predictions: pd.DataFrame,
    predictions_column_names: list[str],
    db_table_name: str,
    data_timestamps: pd.Timestamp,
    data_manager_config: dict[str, Any],
) -> None:
    """
    Save predictions to the SQLite database using DataManager.

    Args:
        predictions : pd.DataFrame containing predictions and timestamps
        predictions_column_names: List of column names to save the predictions to
        db_table_name: Name of the table to save the predictions to
        data_timestamps: Data timestamps
        data_manager_config: DataManager configuration dictionary to save the predictions to
    """
    # Initialize DataManager
    data_manager = DataManager(data_manager_config)
    # Convert input timestamps to pandas datetime
    timestamps = pd.to_datetime(data_timestamps["Timestamps"])

    # Normalize timestamps to string format expected by the database
    # This works for both Series-like inputs and single Timestamp values
    timestamps_str = timestamps.dt.strftime("%Y-%m-%d %H:%M:%S")
    predictions["Timestamps"] = timestamps_str

    # Create predictions DataFrame
    predictions_df = pd.DataFrame(
        {
            "Timestamps": timestamps_str,
            **{
                col: predictions[col].values.ravel() for col in predictions_column_names
            },
        }
    )
    # Save to predictions table
    data_manager.insert_data_to_db(new_data=predictions_df, table_name=db_table_name)
