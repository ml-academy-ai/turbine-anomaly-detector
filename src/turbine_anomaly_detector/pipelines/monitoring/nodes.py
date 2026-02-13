import numpy as np
import pandas as pd
from typing import Optional

def get_wasserstein_distance_1d(
    reference_df: pd.DataFrame,
    monitored_df: pd.DataFrame,
    feature_col: str,
    bins: Optional[int] = None,
) -> float:
    """
    Histogram-based approximation of 1D Wasserstein distance
    for a specific feature column.
    """

    reference = reference_df[feature_col].dropna().to_numpy()
    monitored = monitored_df[feature_col].dropna().to_numpy()

    full_dataset = np.concatenate((reference, monitored))

    if bins is None:
        _, bin_edges = np.histogram(full_dataset, bins="doane")
    else:
        bin_edges = np.linspace(
            min(reference.min(), monitored.min()),
            max(reference.max(), monitored.max()),
            bins + 1
        )

    ref_hist, _ = np.histogram(reference, bins=bin_edges)
    mon_hist, _ = np.histogram(monitored, bins=bin_edges)

    ref_p = ref_hist / ref_hist.sum()
    mon_p = mon_hist / mon_hist.sum()

    ref_cdf = np.cumsum(ref_p)
    mon_cdf = np.cumsum(mon_p)

    bin_widths = np.diff(bin_edges)

    return float(np.sum(np.abs(ref_cdf - mon_cdf) * bin_widths))

def get_retraining_trigger(
    wasserstein_distance: float,
    threshold: float,
) -> bool:
    """
    Determine if retraining is needed based on Wasserstein distance.
    """
    if wasserstein_distance > threshold:
        return 1
    else:
        return 0