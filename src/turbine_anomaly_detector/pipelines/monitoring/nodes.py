"""Monitoring pipeline nodes."""
import pandas as pd
import numpy as np

def compute_anomaly_metrics(y_pred: pd.Series, y_true: pd.Series) -> dict[str, float]:
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
    mape = np.abs(y_true - y_pred) / (y_true + 1e-8) * 100
    return mape
