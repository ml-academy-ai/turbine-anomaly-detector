import copy
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import no_update

from app_data_manager.data_manager import DataManager
from app_data_manager.utils import read_config

# Configuration (same as home page: parameters.yml)
project_root = Path(__file__).resolve().parents[2]
parameters_path = project_root / "conf" / "base" / "parameters.yml"
config = read_config(parameters_path)


def load_prod_data(n_data_points: int = 100000, anomaly_error_type: str = "mape") -> pd.DataFrame:
    """
    Load last N rows from predictions, errors, anomalies, raw_data; merge on Timestamps.
    Returns only DB columns: Timestamps, predict_power, mape, anomaly, Power (if present).
    """
    data_manager = DataManager(config["data_manager"])
    predictions = data_manager.get_last_n_points(n_data_points, table_name="predictions")
    errors = data_manager.get_last_n_points(n_data_points, table_name="errors")
    anomalies = data_manager.get_last_n_points(n_data_points, table_name="anomalies")
    raw_data = data_manager.get_last_n_points(n_data_points, table_name="raw_data")
    df = predictions.copy()
    df = df.merge(
        errors[[
            "Timestamps", 
            anomaly_error_type, 
            f"rolling_{anomaly_error_type}"
            ]].drop_duplicates(subset=["Timestamps"]),
        on="Timestamps",
        how="left",
    )
    df = df.merge(
        anomalies[["Timestamps", "anomaly"]].drop_duplicates(subset=["Timestamps"]),
        on="Timestamps",
        how="left",
    )

    df = df.merge(
        raw_data[["Timestamps", "Power"]].drop_duplicates(subset=["Timestamps"]), 
        on="Timestamps", 
        how="left",
    )
    df.drop_duplicates(subset=["Timestamps"], inplace=True)
    df["true_value"] = df["Power"] if "Power" in df.columns else df["predict_power"]
    df["prediction"] = df["predict_power"]
    return df.sort_values("Timestamps").reset_index(drop=True)


def create_error_plot(
    df: pd.DataFrame,
    metric_threshold: float,
    anomaly_error_type: str = "mape",
    rolling_window: int = 5,
) -> go.Figure:
    """Plot error column, rolling error, threshold line, and anomaly markers."""

    x_min, x_max = df["Timestamps"].min(), df["Timestamps"].max()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["Timestamps"],
            y=df[anomaly_error_type],
            name=anomaly_error_type.upper(),
            mode="lines",
            line=dict(color="#60a5fa", width=1.5),
            opacity=0.6,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["Timestamps"],
            y=df[f"rolling_{anomaly_error_type}"],
            name=f"{anomaly_error_type.upper()} Rolling ({rolling_window} pts)",
            mode="lines",
            line=dict(color="#2563eb", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[x_min, x_max],
            y=[metric_threshold, metric_threshold],
            name=f"Threshold: {metric_threshold:.3f}",
            mode="lines",
            line=dict(color="#111827", width=2.5, dash="dash"),
        )
    )
    anomaly_mask = df["anomaly"] == 1
    df_anom = df.loc[anomaly_mask]
    y_anom = df_anom[f"rolling_{anomaly_error_type}"]
    fig.add_trace(
        go.Scatter(
            x=df_anom["Timestamps"],
            y=y_anom,
            name="Anomaly",
            mode="markers",
            marker=dict(
                color="#dc2626",
                size=10,
                symbol="circle",
                line=dict(width=2, color="#dc2626"),
            ),
        )
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=30, b=40),
        height=None,
        showlegend=True,
        xaxis_title="Time",
        yaxis_title="Mean Absolute Percentage Error",
        xaxis=dict(range=[x_min, x_max], gridcolor="#CBD5E1", linecolor="#E3E8EF"),
        yaxis=dict(gridcolor="#CBD5E1", linecolor="#E3E8EF"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color="#1B1D23", size=12),
    )
    return fig


def create_timeseries_plot(df: pd.DataFrame) -> go.Figure:
    """Plot DB columns only: Power (true) and predict_power. No computed columns."""
    if df.empty or "Timestamps" not in df.columns or "predict_power" not in df.columns:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_white",
            xaxis_title="Time",
            yaxis_title="Power",
            annotations=[
                dict(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            ],
        )
        return fig
    x_min, x_max = df["Timestamps"].min(), df["Timestamps"].max()
    fig = go.Figure()
    if "Power" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Timestamps"],
                y=df["Power"],
                name="Power",
                mode="lines",
                line=dict(color="#16A34A", width=2.5),
            )
        )
    fig.add_trace(
        go.Scatter(
            x=df["Timestamps"],
            y=df["predict_power"],
            name="predict_power",
            mode="lines",
            line=dict(color="#2563eb", width=2.5),
        )
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=30, b=40),
        height=None,
        showlegend=True,
        xaxis_title="Time",
        yaxis_title="Power",
        xaxis=dict(range=[x_min, x_max], gridcolor="#CBD5E1", linecolor="#E3E8EF"),
        yaxis=dict(gridcolor="#CBD5E1", linecolor="#E3E8EF"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color="#1B1D23", size=12),
    )
    return fig


def sync_xaxis(relayout_data, current_figure):
    """Copy x-axis range from relayout_data into current_figure. Returns (updated_figure, x_range) or (no_update, no_update)."""
    if not relayout_data or not current_figure:
        return no_update, no_update

    keys = ("xaxis.range[0]", "xaxis.range", "xaxis.autorange")
    if not any(k in relayout_data for k in keys):
        return no_update, no_update

    updated_figure = copy.deepcopy(current_figure)
    if "xaxis" not in updated_figure["layout"]:
        updated_figure["layout"]["xaxis"] = {}

    if "xaxis.autorange" in relayout_data:
        updated_figure["layout"]["xaxis"].pop("range", None)
        updated_figure["layout"]["xaxis"]["autorange"] = True
        return updated_figure, None

    x_range = None
    if "xaxis.range[0]" in relayout_data and "xaxis.range[1]" in relayout_data:
        x_range = [relayout_data["xaxis.range[0]"], relayout_data["xaxis.range[1]"]]
    elif "xaxis.range" in relayout_data and isinstance(relayout_data["xaxis.range"], list):
        x_range = relayout_data["xaxis.range"]

    if x_range:
        updated_figure["layout"]["xaxis"]["range"] = x_range
        updated_figure["layout"]["xaxis"]["autorange"] = False
        return updated_figure, x_range

    return no_update, no_update