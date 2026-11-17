"""AERIS Local Database Module
Optional SQLite local storage for persistence of cleaned datasets and audit records.
"""

from typing import Dict, List, Optional
import os
import sqlite3
import pandas as pd


DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "processed", "aeris_local_storage.db"
)


def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Returns a SQLite connection, ensuring the parent directory exists."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    return sqlite3.connect(db_path)


def init_database(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes schema for audit log table if not present."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                dataset_name TEXT,
                raw_records INTEGER,
                cleaned_records INTEGER,
                duplicates_removed INTEGER,
                negative_corrected INTEGER,
                cities_count INTEGER,
                date_range TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def save_dataset_to_db(
    df: pd.DataFrame,
    table_name: str = "cleaned_air_quality",
    db_path: str = DEFAULT_DB_PATH,
    if_exists: str = "replace"
) -> bool:
    """Saves a cleaned DataFrame to a local SQLite table."""
    conn = None
    try:
        init_database(db_path)
        conn = get_db_connection(db_path)
        # Convert datetime columns to ISO string for clean SQLite storage
        save_df = df.copy()
        if "Date" in save_df.columns:
            save_df["Date"] = pd.to_datetime(save_df["Date"]).dt.strftime("%Y-%m-%d")
        save_df.to_sql(table_name, conn, if_exists=if_exists, index=False)
        return True
    except Exception as e:
        print(f"Error saving dataset to SQLite: {e}")
        return False
    finally:
        if conn:
            conn.close()


def load_dataset_from_db(
    table_name: str = "cleaned_air_quality",
    db_path: str = DEFAULT_DB_PATH
) -> Optional[pd.DataFrame]:
    """Loads a stored table from SQLite into a DataFrame."""
    if not os.path.exists(db_path):
        return None

    conn = None
    try:
        conn = get_db_connection(db_path)
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df
    except Exception as e:
        print(f"Error loading dataset from SQLite: {e}")
        return None
    finally:
        if conn:
            conn.close()


def list_tables_in_db(db_path: str = DEFAULT_DB_PATH) -> List[str]:
    """Lists all user tables in the SQLite database."""
    if not os.path.exists(db_path):
        return []
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    except Exception:
        return []
    finally:
        if conn:
            conn.close()


def log_data_audit(summary_dict: Dict, dataset_name: str = "User Upload", db_path: str = DEFAULT_DB_PATH) -> None:
    """Logs data cleaning metrics to the audit_logs table."""
    conn = None
    try:
        init_database(db_path)
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (
                dataset_name, raw_records, cleaned_records, duplicates_removed,
                negative_corrected, cities_count, date_range
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            dataset_name,
            summary_dict.get("Total Raw Records", 0),
            summary_dict.get("Cleaned Records", 0),
            summary_dict.get("Duplicates Removed", 0),
            summary_dict.get("Negative Values Corrected", 0),
            summary_dict.get("Cities Count", 0),
            str(summary_dict.get("Date Range", "N/A"))
        ))
        conn.commit()
    except Exception as e:
        print(f"Failed to record audit log: {e}")
    finally:
        if conn:
            conn.close()
