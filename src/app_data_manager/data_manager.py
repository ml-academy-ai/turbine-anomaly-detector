import sqlite3 as sq
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

# Add project root to Python path for imports
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))


class DataManager:
    """
    Manages SQLite database operations for raw sensor data and model predictions.

    This class provides a unified interface for storing and querying time-series data
    in a SQLite database. It handles:
    - Database initialization with configurable schemas
    - Raw sensor data storage from turbines
    - Model prediction storage with timestamps
    - Time-series queries (by range or last N points)
    - Idempotent data insertion using UPSERT pattern

    Uses SQLite default journal mode (DELETE) for simpler operation across
    Docker bind mounts. All operations are designed to be safe for production
    use with proper error handling.
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize DataManager with configuration dictionary.

        Args:
            config: The 'data_manager' section from parameters.yml
        """
        self.config = config

    def _build_schema_sql(self, schema: list[dict[str, Any]]) -> str:
        """
        Build SQL column definitions from schema configuration.

        Converts a list of column dictionaries into SQL CREATE TABLE syntax.
        Each column dict can specify: name, type, not_null, primary_key.

        Args:
            schema: List of column definitions, e.g.:
                [{"name": "Timestamps", "type": "TEXT", "primary_key": True}, ...]

        Returns:
            Comma-separated SQL column definitions string.
        """
        definitions = []
        for col in schema:
            col_def = f"{col['name']} {col['type']}"
            if col.get("not_null", False):
                col_def += " NOT NULL"
            if col.get("primary_key", False):
                col_def += " PRIMARY KEY"
            definitions.append(col_def)
        return ", ".join(definitions)

    def _get_connection(self, timeout: int = 30, max_retries: int = 5) -> sq.Connection:
        """
        Get database connection using SQLite default journal mode (DELETE).

        Retries on DatabaseError (e.g. "file is not a database") to handle the
        race when app-stream-data resets the DB while other services are reading.

        Args:
            timeout: Seconds to wait before raising timeout error (default: 30).
            max_retries: Number of retries on transient DB errors (default: 5).

        Returns:
            SQLite connection object.
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                conn = sq.connect(self.config["sqlite_db_path"], timeout=timeout)
                return conn
            except sq.DatabaseError as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(1)
        assert last_error is not None
        raise last_error from last_error

    def init_raw_db_table(self) -> None:
        """
        Recreate the raw data table and load historical data from parquet file.

        This method performs a complete reset:
        1. Creates database directory if needed
        2. Deletes existing database file (if present)
        3. Loads historical data from parquet
        4. Creates table with schema from config
        5. Populates table with historical data

        WARNING: This is a destructive operation that deletes existing data.
        Use only during initial setup or when you need to reset the database.

        Raises:
            FileNotFoundError: If historical data parquet file doesn't exist.
            sqlite3.Error: If database operations fail.
        """
        db_path = Path(self.config["sqlite_db_path"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.unlink(missing_ok=True)

        history_path = (
            Path(self.config["history_data_folder"])
            / self.config["history_data_filename"]
        )
        df = pd.read_parquet(history_path)

        with self._get_connection() as conn:
            schema_sql = self._build_schema_sql(self.config["raw_data_table_schema"])
            conn.execute(
                f"CREATE TABLE {self.config['raw_data_table_name']} ({schema_sql})"
            )
            df.to_sql(
                self.config["raw_data_table_name"],
                conn,
                if_exists="append",
                index=False,
            )

    def init_predictions_db_table(self) -> None:
        """
        Create predictions table and timestamp index if they don't exist.

        This method is idempotent - safe to call multiple times. It creates:
        1. Predictions table with schema from config
        2. Index on Timestamps column for faster queries

        The index significantly speeds up:
        - Range queries (get_data_by_timestamp_range)
        - Ordering queries (get_last_n_points)
        - JOIN operations

        Unlike init_raw_db_table, this does NOT delete existing data.
        """
        Path(self.config["sqlite_db_path"]).parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            schema_sql = self._build_schema_sql(self.config["predictions_table_schema"])
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self.config['predictions_table_name']} ({schema_sql})"
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_timestamps "
                f"ON {self.config['predictions_table_name']} (Timestamps)"
            )

    def init_errors_db_table(self) -> None:
        """
        Create errors table and timestamp index if they don't exist.

        This method is idempotent - safe to call multiple times. It creates:
        1. Errors table with schema from config
        2. Index on Timestamps column for faster queries

        The index significantly speeds up:
        - Range queries (get_data_by_timestamp_range)
        - Ordering queries (get_last_n_points)
        - JOIN operations

        Unlike init_raw_db_table, this does NOT delete existing data.
        """
        Path(self.config["sqlite_db_path"]).parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            schema_sql = self._build_schema_sql(self.config["errors_table_schema"])
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self.config['errors_table_name']} ({schema_sql})"
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_timestamps "
                f"ON {self.config['errors_table_name']} (Timestamps)"
            )

    def init_anomalies_db_table(self) -> None:
        """
        Create anomalies table and timestamp index if they don't exist.

        This method is idempotent - safe to call multiple times. It creates:
        1. Anomalies table with schema from config
        2. Index on Timestamps column for faster queries

        The index significantly speeds up:
        - Range queries (get_data_by_timestamp_range)
        - Ordering queries (get_last_n_points)
        - JOIN operations

        Unlike init_raw_db_table, this does NOT delete existing data.
        """
        Path(self.config["sqlite_db_path"]).parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            schema_sql = self._build_schema_sql(self.config["anomalies_table_schema"])
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self.config['anomalies_table_name']} ({schema_sql})"
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_timestamps "
                f"ON {self.config['anomalies_table_name']} (Timestamps)"
            )

    def init_retraining_trigger_db_table(self) -> None:
        """
        Create retraining trigger table and timestamp index if they don't exist.
        """
        Path(self.config["sqlite_db_path"]).parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            schema_sql = self._build_schema_sql(
                self.config["retraining_trigger_table_schema"]
            )
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self.config['retraining_trigger_table_name']} ({schema_sql})"
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_timestamps "
                f"ON {self.config['retraining_trigger_table_name']} (Timestamps)"
            )

    def get_last_n_points(self, n: int, table_name: str) -> pd.DataFrame:
        """
        Retrieve the last N data points from the specified table.

        Queries the database for the most recent N records ordered by timestamp,
        then returns them in chronological order (oldest first).

        Args:
            n: Number of most recent points to retrieve. Must be positive.
               Returns empty DataFrame if n <= 0.
            table_name: Table to query (e.g., raw_data_table_name or predictions_table_name).

        Returns:
            DataFrame with last N rows, ordered chronologically (oldest first).
            Empty DataFrame if n <= 0 or table is empty.
        """
        if n <= 0:
            return pd.DataFrame()

        with self._get_connection() as conn:
            df = pd.read_sql_query(
                f"SELECT * FROM {table_name} ORDER BY Timestamps DESC LIMIT ?",  # ? is a placeholder for n
                conn,
                params=[n],  # n is the number of points to retrieve
            )
            return df.iloc[::-1].reset_index(drop=True)

    def insert_data_to_db(
        self,
        new_data: pd.DataFrame,
        table_name: str,
    ) -> None:
        """
        Insert or update rows using UPSERT pattern (idempotent writes).

        UPSERT (INSERT ... ON CONFLICT DO UPDATE) ensures:
        - New rows are inserted normally
        - Existing rows (same Timestamps) are updated with new values
        - No duplicate timestamps can exist

        The Timestamps column acts as the primary key for conflict detection.
        Timestamps are normalized to "YYYY-MM-DD HH:MM:SS" format to prevent
        duplicates from formatting differences.

        Args:
            new_data: DataFrame to insert/update. MUST include 'Timestamps' column.
            table_name: Target table (e.g., raw_data_table_name or predictions_table_name).
        """
        # Early return if no data to process
        if new_data is None or new_data.empty:
            return

        # Validate that Timestamps column exists (required for UPSERT)
        if "Timestamps" not in new_data.columns:
            raise ValueError("Column `Timestamps` is required for all database writes.")

        # Work on a copy to avoid mutating the original DataFrame
        df = new_data.copy()

        # Normalize timestamps to consistent format to prevent duplicates
        # Converts various formats (ISO, pandas Timestamp, etc.) to "YYYY-MM-DD HH:MM:SS"
        df["Timestamps"] = pd.to_datetime(df["Timestamps"]).dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Extract column names for SQL statement construction
        cols = list(df.columns)

        # Build quoted column list for INSERT statement: "col1", "col2", ...
        # Quoting prevents issues with reserved words or special characters
        col_list = ", ".join(f'"{c}"' for c in cols)

        # Build parameterized placeholders: ?, ?, ? (one per column)
        # Parameterized queries prevent SQL injection and improve performance
        placeholders = ", ".join(["?"] * len(cols))

        # Identify columns to update on conflict (all except Timestamps)
        # Timestamps is the primary key, so it doesn't need updating
        update_cols = [c for c in cols if c != "Timestamps"]

        # Edge case: if only Timestamps column exists, nothing to update
        if not update_cols:
            return

        # Build SET clause for UPDATE part of UPSERT
        # SQLite's "excluded" refers to the values that would have been inserted
        # Example: "y_pred" = excluded."y_pred", "model_version" = excluded."model_version"
        set_clause = ", ".join(f'"{c}" = excluded."{c}"' for c in update_cols)

        # Construct the UPSERT SQL statement
        # INSERT: Attempts to insert new rows
        # ON CONFLICT("Timestamps"): Triggers when Timestamps already exists
        # DO UPDATE SET: Updates existing row with new values from excluded
        sql = (
            f'INSERT INTO "{table_name}" ({col_list}) '
            f"VALUES ({placeholders}) "
            f'ON CONFLICT("Timestamps") DO UPDATE SET {set_clause}'
        )

        # Execute batch UPSERT operation
        with self._get_connection() as conn:
            # executemany() efficiently inserts/updates multiple rows at once
            # values.tolist() converts DataFrame to list of tuples: [(row1), (row2), ...]
            # Column order matches cols list, ensuring correct value assignment
            conn.executemany(sql, df[cols].values.tolist())
            # Explicit commit ensures all changes are persisted to disk
            conn.commit()

    def get_data_since_timestamp(
        self,
        start_timestamp: str | pd.Timestamp,
        table_name: str,
    ) -> pd.DataFrame:
        """
        Retrieve all data points from a given timestamp until the latest available.

        Args:
            start_timestamp: Start timestamp (inclusive). Can be string or pd.Timestamp.
                           All rows with Timestamps >= this value will be returned.
            table_name: Table to query (e.g., raw_data_table_name or predictions_table_name).

        Returns:
            DataFrame with all rows where Timestamps >= start_timestamp,
            ordered chronologically (oldest first). Empty DataFrame if no matches.
        """
        with self._get_connection() as conn:
            return pd.read_sql_query(
                f"SELECT * FROM {table_name} "
                f"WHERE Timestamps >= ? "
                f"ORDER BY Timestamps ASC",
                conn,
                params=[str(start_timestamp)],
            )

    def get_data_by_timestamp_range(
        self,
        start_timestamp: str | pd.Timestamp,
        end_timestamp: str | pd.Timestamp,
        table_name: str,
    ) -> pd.DataFrame:
        """
        Retrieve data points within a timestamp range (inclusive on both ends).

        Args:
            start_timestamp: Start of range (inclusive). Can be string or pd.Timestamp.
            end_timestamp: End of range (inclusive). Same format as start_timestamp.
            table_name: Table to query (e.g., raw_data_table_name or predictions_table_name).

        Returns:
            DataFrame with rows where Timestamps is between start and end,
            ordered chronologically (oldest first). Empty DataFrame if no matches.
        """
        with self._get_connection() as conn:
            return pd.read_sql_query(
                f"SELECT * FROM {table_name} "
                f"WHERE Timestamps >= ? AND Timestamps <= ? "
                f"ORDER BY Timestamps ASC",
                conn,
                params=[str(start_timestamp), str(end_timestamp)],
            )
