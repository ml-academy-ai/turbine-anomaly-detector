import pandas as pd
import numpy as np
from typing import Any
from app_data_manager.data_manager import DataManager


def rename_columns(df: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    """
    Rename columns in a dataframe.
    """
    return df.rename(columns=columns)

def drop_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Drop columns in a dataframe.
    """
    return df.drop(columns=columns)

def remove_diff_outliers(df: pd.DataFrame, diff_thresholds: dict[str, float]) -> pd.DataFrame:
    """
    Remove outliers based on absolute first-order diff and forward-fill the gaps.
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    diff_thresholds : dict[str, float]
        Dictionary of column names and their corresponding absolute diff thresholds.

    Returns
    -------
    df_clean : pd.DataFrame
        Cleaned dataframe with forward fill.
    """
    df_clean = df.copy()

    for col, threshold in diff_thresholds.items():
        # 1. Compute absolute diff
        diff_vals = df_clean[col].diff(1).abs()

        # 2. Outlier mask
        outlier_mask = diff_vals > threshold
        outlier_idx = df_clean.index[outlier_mask]

        # 3. Remove outliers
        df_clean.loc[outlier_idx, col] = np.nan

        # 4. Forward fill (and backfill if needed)
        df_clean[col] = df_clean[col].ffill().bfill()

        return df_clean

    
def smooth_signal(df: pd.DataFrame, columns: str, window: int, method: str = "mean") -> pd.DataFrame:
    """
    Smooth a time-series column using rolling mean or median.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    column : str
        Column to smooth.
    window : int
        Rolling window size.
    method : str
        "mean"  -> rolling mean filter
        "median" -> rolling median filter (robust smoothing)

    Returns
    -------
    df_smoothed : pd.DataFrame
        DataFrame with smoothed column.
    """

    df_smoothed = df.copy()

    for col in columns:
        if method == "mean":
            df_smoothed[col] = df_smoothed[col].rolling(
                window=window, min_periods=1, center=False
            ).mean()

        elif method == "median":
            df_smoothed[col] = df_smoothed[col].rolling(
                window=window, min_periods=1, center=False
            ).median()

        else:
            raise ValueError("method must be 'mean' or 'median'")

    return df_smoothed


def add_lag_features(df: pd.DataFrame, lags_dict: dict[str, list[int]], drop_na=False) -> pd.DataFrame:
    """
    Add lag features to DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    lags_dict : dict[str, list[int]]
        Dictionary mapping column names to lists of lag periods.
        For example: {'column1': [1, 2, 3], 'column2': [1, 5]}.
    drop_na : bool, optional
        If True, drop rows with NaN values. If False, backward fill NaN values.
        Default is False.

    Returns
    -------
    pd.DataFrame
        DataFrame with lag features added. Lag features are named as '{column}_lag{lag}'.
    """
    df_result = df.copy()

    # Create lag features
    for col, lags in lags_dict.items():
        for lag in lags:
            df_result[f"{col}_lag{lag}"] = df_result[col].shift(lag)

    if drop_na:
        return df_result.dropna()
    else:
        return df_result.bfill()  # Backward fill NaNs


def add_rolling_features(
    df: pd.DataFrame,
    stats_window_dict: dict[str, dict[str, list]],
    drop_na=False,
) -> pd.DataFrame:
    """
    Add rolling features to DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    stats_window_dict : dict[str, dict[str, list]]
        Dictionary mapping column names to dictionaries containing 'windows' and 'stats'.
        Each inner dictionary must have:
        - 'windows': list of window sizes (integers)
        - 'stats': list of statistics to compute
        Available statistics: 'mean', 'median', 'std', 'min', 'max', 'skew', 'kurt'.
        For example: {'column1': {'windows': [7, 14], 'stats': ['mean', 'std']},
                     'column2': {'windows': [5, 10], 'stats': ['median', 'max']}}.
    drop_na : bool, optional
        If True, drop rows with NaN values. If False, backward fill NaN values.
        Default is False.

    Returns
    -------
    pd.DataFrame
        DataFrame with rolling features added. Rolling features are named as
        '{column}_roll{window}_{stat}'.
    """
    df_result = df.copy()

    for col in stats_window_dict.keys():
        for window in stats_window_dict[col]["windows"]:
            rolling = df_result[col].rolling(window)
            for stat in stats_window_dict[col]["stats"]:
                if stat == "mean":
                    df_result[f"{col}_roll{window}_mean"] = rolling.mean()
                elif stat == "median":
                    df_result[f"{col}_roll{window}_median"] = rolling.median()
                elif stat == "std":
                    df_result[f"{col}_roll{window}_std"] = rolling.std()
                elif stat == "min":
                    df_result[f"{col}_roll{window}_min"] = rolling.min()
                elif stat == "max":
                    df_result[f"{col}_roll{window}_max"] = rolling.max()
                elif stat == "skew":
                    df_result[f"{col}_roll{window}_skew"] = rolling.skew()
                elif stat == "kurt":
                    df_result[f"{col}_roll{window}_kurt"] = rolling.kurt()
    if drop_na:
        return df_result.dropna()
    else:
        return df_result.bfill()  # Backward fill NaNs


def get_features_and_target(
    df: pd.DataFrame, target: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Get the features and target from the dataframe.
    """
    x = df.drop(columns=target).copy()
    y = pd.DataFrame(df[target].copy(), columns=[target])
    return x, y


def load_training_data_from_db(
    start_timestamp: str,
    table_name: str,
    data_manager_config: dict[str, Any],
) -> pd.DataFrame:
    """
    Load training data from SQLite database by timestamp range.

    Args:
        start_timestamp: Start timestamp (inclusive)
        end_timestamp: End timestamp (inclusive)
        table_name: Name of the table to read from
        data_manager_config: DataManager configuration dictionary

    Returns:
        DataFrame containing data within the timestamp range
    """
    data_manager = DataManager(data_manager_config)

    df = data_manager.get_data_since_timestamp(
        start_timestamp=start_timestamp,
        table_name=table_name,
    )
    return df


def load_inference_batch(
    batch_size: int,
    table_name: str,
    data_manager_config: dict[str, Any],
) -> pd.DataFrame:
    """
    Get the last N data points from SQLite database.

    Args:
        batch_size: Number of points to retrieve
        table_name: Name of the table to read from
        data_manager_config: DataManager configuration dictionary

    Returns:
        DataFrame containing the last N rows, ordered by Timestamps
    """
    data_manager = DataManager(data_manager_config)
    df = data_manager.get_last_n_points(n=batch_size, table_name=table_name)
    return df

def get_data_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get the current timestamp from the dataframe.
    """
    return pd.DataFrame(df["Timestamps"].values, columns=["Timestamps"])