import sqlite3
import pandas as pd
import os
from datetime import datetime
from app.utils.logging_utils import log_message
from .base import BasePriceCRUD # Import the base class
from typing import List, Dict, Tuple, Optional, Any

class SQLitePriceCRUD(BasePriceCRUD):
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                price REAL NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def save_price_entry(self, price_value: float) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            cursor.execute("INSERT INTO prices (timestamp, price) VALUES (?, ?)", (current_timestamp, price_value))
            conn.commit()
        except sqlite3.Error as e:
            log_message(f"SQLite Error saving price: {e}")
        finally:
            conn.close()

    def get_all_price_entries_df(self) -> pd.DataFrame:
        conn = self._get_connection()
        try:
            df = pd.read_sql_query("SELECT timestamp as date, price FROM prices ORDER BY timestamp ASC", conn)
        except (pd.io.sql.DatabaseError, sqlite3.Error) as e:
            log_message(f"SQLite Error loading price history to DataFrame: {e}")
            df = pd.DataFrame(columns=["date", "price"])
        finally:
            conn.close()
        return df

    def get_latest_price_entry(self) -> Optional[Tuple[str, float]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT timestamp, price FROM prices ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return row if row else None
        except sqlite3.Error as e:
            log_message(f"SQLite Error fetching latest price: {e}")
            return None
        finally:
            conn.close()

    def delete_all_prices(self) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM prices")
            conn.commit()
            log_message("All price entries deleted from SQLite.")
        except sqlite3.Error as e:
            log_message(f"SQLite Error deleting all prices: {e}")
            conn.rollback()
        finally:
            conn.close()

    def bulk_insert_prices(self, price_entries: List[Dict[str, Any]]) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            data_to_insert = [(entry['timestamp'], entry['price']) for entry in price_entries]
            cursor.executemany("INSERT INTO prices (timestamp, price) VALUES (?, ?)", data_to_insert)
            conn.commit()
            log_message(f"Bulk inserted {len(data_to_insert)} price entries into SQLite.")
        except sqlite3.Error as e:
            log_message(f"SQLite Error bulk inserting prices: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_price_stats(self) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(price),
                    MIN(price),
                    MAX(price),
                    AVG(price)
                FROM prices
                WHERE price IS NOT NULL
            """)
            stats = cursor.fetchone()
            count, min_price, max_price, avg_price = stats if stats else (0, None, None, None)
            
            if count == 0:
                return {"total_entries": 0, "min_price": None, "max_price": None, "average_price": None}
            return {
                "total_entries": count,
                "min_price": min_price,
                "max_price": max_price,
                "average_price": round(avg_price, 2) if avg_price is not None else None
            }
        except sqlite3.Error as e:
            log_message(f"SQLite Database error calculating stats: {str(e)}")
            # Consider re-raising a custom DB error or returning a default error structure
            raise # Re-raise to be handled by service/API layer
        finally:
            conn.close()