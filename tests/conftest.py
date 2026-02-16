import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_df():
    return pd.DataFrame({"col1": [10, 20, 30, 40], "col2": [1, 2, 3, 4]})


@pytest.fixture
def dataset_with_outliers():
    """Small synthetic dataset with outliers in one column only."""
    n = 15
    timestamps = pd.date_range("2024-01-01", periods=n, freq="h")
    # Smooth series
    t = np.linspace(0, 2 * np.pi, n)
    power = 50 + 10 * np.sin(t)

    df = pd.DataFrame({"power": power, "Timestamps": timestamps})

    # Outliers in power only
    df.loc[5, "power"] = 200   # spike
    df.loc[10, "power"] = -10  # impossible drop
    return df