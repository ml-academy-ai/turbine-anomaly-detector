import pandas as pd


def rename_columns(df: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    """
    Rename columns in a dataframe.
    """
    return df.rename(columns=columns)