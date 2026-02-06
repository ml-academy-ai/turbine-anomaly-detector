# Data Manager Development


### Explain the slides including `Database Initialization` (10 mins)

# Create a directory `src/app_data_manager`, inside `__init__.py`, `app.py`, 'data_manager.py'\

### Create `DataManager` class with ``
```python
import sqlite3 as sq
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# Add project root to Python path for imports
project_root = Path(__file__).resolve().parents[2]
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

    The class uses Write-Ahead Logging (WAL) mode for better concurrency, allowing
    multiple readers while writes occur. All operations are designed to be safe
    for production use with proper error handling.
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize DataManager with configuration dictionary.

        Args:
            config: The 'data_manager' section from parameters.yml containing:
                - sqlite_db_path: Path to SQLite database file
                - raw_data_table_name: Name of raw data table
                - predictions_table_name: Name of predictions table
                - raw_data_table_schema: List of column definitions for raw data
                - predictions_table_schema: List of column definitions for predictions
                - history_data_folder: Folder containing historical data parquet file
                - history_data_filename: Name of historical data parquet file
        """
        self.config = config
        self.db_path = self.config["sqlite_db_path"]
        self.raw_data_table_name = self.config["raw_data_table_name"]
        self.predictions_table_name = self.config["predictions_table_name"]
        self.raw_data_table_schema = self.config["raw_data_table_schema"]
        self.predictions_table_schema = self.config["predictions_table_schema"]
```

### Add basic configuration to the config
```yaml
data_manager:
  history_data_folder: data/01_raw
  history_data_filename: df_train_test.parquet
  inference_data_folder: data/01_raw
  inference_data_filename: df_prod.parquet
  sqlite_db_path: data/sqlite/app.db
  raw_data_table_name: raw_data
  predictions_table_name: predictions
```

### Add a method that connects to the database
```python
 def _get_connection(self, timeout: int = 30):
        """
        Get database connection with Write-Ahead Logging (WAL) mode enabled.

        WAL mode allows multiple readers and one writer simultaneously, improving
        performance in concurrent scenarios. The timeout prevents indefinite blocking
        if the database is locked by another process.

        Args:
            timeout: Seconds to wait before raising timeout error (default: 30).

        Returns:
            SQLite connection object with WAL mode enabled.
        """
        conn = sq.connect(self.db_path, timeout=timeout)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn
```

### Add Schema of the First Table - Raw Data Table
```yaml
  raw_data_table_schema:
    - name: Timestamps
      type: TEXT
      primary_key: true
    - name: WindSpeed
      type: REAL
    - name: WindDirAbs
      type: REAL
    - name: WindDirRel
      type: REAL
    - name: Power
      type: REAL
    - name: Pitch
      type: REAL
    - name: GenRPM
      type: REAL
    - name: RotorRPM
      type: REAL
    - name: EnvirTemp
      type: REAL
    - name: NacelTemp
      type: REAL
    - name: GearOilTemp
      type: REAL
    - name: GearBearTemp
      type: REAL
    - name: GenPh1Temp
      type: REAL
    - name: GenBearTemp
      type: REAL
  predictions_table_schema:
    - name: Timestamps
      type: TEXT
      primary_key: true
      not_null: true
    - name: predicted_power
      type: REAL
      not_null: true
```

### Add a method that builds a schema to the SQL syntax
```python
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
```

### Add a method that inits and populates the `raw_data_table`
```python
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
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.db_path).unlink(missing_ok=True)

        history_path = Path(self.config["history_data_folder"]) / self.config["history_data_filename"]
        df = pd.read_parquet(history_path)

        with self._get_connection() as conn:
            schema_sql = self._build_schema_sql(self.raw_data_table_schema)
            conn.execute(f"CREATE TABLE {self.raw_data_table_name} ({schema_sql})")
            df.to_sql(self.raw_data_table_name, conn, if_exists="append", index=False)
```

### Add `app_data_manager/utils.py` the config reader
```python
from pathlib import Path

import yaml


def read_config(config_path: str | Path) -> dict:
    """
    Reads a YAML configuration file and returns it as a dictionary.

    Parameters:
    ----------
    config_path : str or Path
        Path to the YAML file.

    Returns:
    -------
    dict
        Parsed YAML content as a dictionary.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r") as f:
        return yaml.safe_load(f)
```

### Now, it's time to start the application and check how it works in `app.py`
```python
import os
import sys
from pathlib import Path

import pandas as pd
from data_manager import DataManager  # type: ignore
from utils import read_config  # type: ignore

# Add project root and app_ui directory to path
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))
os.chdir(project_root)


if __name__ == "__main__":
    config = read_config(os.path.join(project_root, "conf", "base", "parameters.yml"))
    data_manager = DataManager(config["data_manager])
    data_manager.init_raw_db_table()
```

### To check if we have written anything to the database, let's make `read_last_n_points` method
```python
def get_last_n_points(self, n: int, table_name: str | None = None) -> pd.DataFrame:
        """
        Retrieve the last N data points from the specified table.

        Queries the database for the most recent N records ordered by timestamp,
        then returns them in chronological order (oldest first).

        Args:
            n: Number of most recent points to retrieve. Must be positive.
               Returns empty DataFrame if n <= 0.
            table_name: Table to query. If None, uses raw_data_table_name.
                       Can be raw_data_table_name or predictions_table_name.

        Returns:
            DataFrame with last N rows, ordered chronologically (oldest first).
            Empty DataFrame if n <= 0 or table is empty.
        """
        if n <= 0:
            return pd.DataFrame()

        with self._get_connection() as conn:
            df = pd.read_sql_query(
                f"SELECT * FROM {table_name} ORDER BY Timestamps DESC LIMIT ?", # ? is a placeholder for n
                conn,
                params=[n], # n is the number of points to retrieve
            )
            return df.iloc[::-1].reset_index(drop=True)
```

### Run the method on the app
```python
if __name__ == "__main__":
    config = read_config(os.path.join(project_root, "conf", "base", "parameters.yml"))
    data_manager = DataManager(config["data_manager])

    data_manager.init_raw_db_table()
    data = data_manager.get_last_n_points(10, table_name="raw_data")
    print(data)
```

### Add `init_prediction_db_table`
```python
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
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            schema_sql = self._build_schema_sql(self.predictions_table_schema)
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self.predictions_table_name} ({schema_sql})"
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_timestamps "
                f"ON {self.predictions_table_name} (Timestamps)"
            )
```

### Let's implement `insert_to_db` method
```python
def insert_data_to_db(
        self,
        new_data: pd.DataFrame,
        table_name: str | None = None,
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
            table_name: Target table. If None, uses raw_data_table_name.
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
        df["Timestamps"] = pd.to_datetime(df["Timestamps"]).dt.strftime("%Y-%m-%d %H:%M:%S")

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
```

### Run the new method in the `app.py`
```python
import os
import sys
from pathlib import Path

import pandas as pd
from data_manager import DataManager  # type: ignore
from utils import read_config  # type: ignore

# Add project root and app_ui directory to path
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))
os.chdir(project_root)


if __name__ == "__main__":
    config = read_config(os.path.join(project_root, "conf", "base", "parameters.yml"))
    data_manager = DataManager(config["data_manager"])

    data_manager.init_raw_db_table()
    data = data_manager.get_last_n_points(10, table_name="raw_data")
    
    inference_data = pd.read_parquet(
        os.path.join(project_root, "data", "01_raw", "df_prod.parquet")
    )
    data_manager.insert_data_to_db(inference_data, table_name="raw_data")
    data_manager.init_predictions_db_table()
```

### Implement `get_data_since_timestamp` for training
```python
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
```

### Check if the data can be read in the `app.py` file
```python
data = data_manager.get_data_since_timestamp(
        start_timestamp="2009-01-01 00:00:00", 
        table_name="raw_data"
        )
    print(data)
```

# Dataflow
### Explain the dataflow slides