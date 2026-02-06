"""Inference pipeline nodes."""
from typing import Any
import pandas as pd
from turbine_anomaly_detector.common.mlflow_utils import load_model_by_alias
from app_data_manager.data_manager import DataManager


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


def save_predictions_to_db(
    y_pred: pd.Series,
    data_timestamps: pd.Timestamp,
    data_manager_config: dict[str, Any],
) -> None:
    """
    Save predictions to the SQLite database using DataManager.

    Args:
        y_pred: Predicted values as a Series
        data_manager_config: DataManager configuration dictionary
    """
    # Initialize DataManager
    data_manager = DataManager(data_manager_config)
    # Convert input timestamps to pandas datetime
    timestamps = pd.to_datetime(data_timestamps["Timestamps"])

    # Normalize timestamps to string format expected by the database
    # This works for both Series-like inputs and single Timestamp values
    timestamps_str = timestamps.dt.strftime("%Y-%m-%d %H:%M:%S")

    # Create predictions DataFrame
    predictions_df = pd.DataFrame(
        {
            "Timestamps": timestamps_str,
            "predict_power": y_pred.values.ravel(),
        }
    )
    # Save to predictions table
    data_manager.insert_data_to_db(
        new_data=predictions_df,
        table_name=data_manager.predictions_table_name
    )
