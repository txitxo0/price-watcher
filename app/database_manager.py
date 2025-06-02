import sqlite3
import pandas as pd
import os
from datetime import datetime

# Centralized database file path
DB_FILE = "./data/price_watcher.db"

# Ensure data directory exists when this module is loaded
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

def init_db():
    """Initialize the SQLite database and create the prices table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
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

def save_price_entry(price_value: float):
    """Save a new price entry into the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        cursor.execute("INSERT INTO prices (timestamp, price) VALUES (?, ?)", (current_timestamp, price_value))
        conn.commit()
    except sqlite3.Error as e:
        # Consider logging this error appropriately
        print(f"Error saving price to database: {e}") # Placeholder for better logging
    finally:
        conn.close()

def load_all_price_history_df() -> pd.DataFrame:
    """Load all price history from the SQLite database into a Pandas DataFrame."""
    conn = sqlite3.connect(DB_FILE)
    try:
        # Aliasing 'timestamp' to 'date' for compatibility with graph generation logic
        df = pd.read_sql_query("SELECT timestamp as date, price FROM prices ORDER BY timestamp ASC", conn)
    except pd.io.sql.DatabaseError: # Handles case where table might be empty or query fails
        df = pd.DataFrame(columns=["date", "price"])
    finally:
        conn.close()
    return df

def get_latest_price_entry() -> tuple | None:
    """Get the most recent price entry (timestamp, price) from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT timestamp, price FROM prices ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return row if row else None
    except sqlite3.Error as e:
        print(f"Error fetching latest price: {e}") # Placeholder for better logging
        return None
    finally:
        conn.close()

def clean_price_history_db():
    """Reduce database size by keeping only the first price entry for a week if prices were unchanged that week."""
    conn = sqlite3.connect(DB_FILE)
    try:
        df_all_history = pd.read_sql_query("SELECT id, timestamp, price FROM prices ORDER BY timestamp ASC", conn)

        if df_all_history.empty:
            print("Price history is empty, skipping cleanup.") # Placeholder for better logging
            return

        df_all_history['datetime_obj'] = pd.to_datetime(df_all_history['timestamp'])
        df_all_history['week_num'] = df_all_history['datetime_obj'].dt.strftime('%Y-%W')

        rows_to_keep = []
        for _week, group_data in df_all_history.groupby('week_num'):
            if group_data['price'].nunique() == 1:
                earliest_entry = group_data.sort_values(by='datetime_obj').iloc[0]
                rows_to_keep.append({'timestamp': earliest_entry['timestamp'], 'price': earliest_entry['price']})
            else:
                for _idx, row_data in group_data.iterrows():
                    rows_to_keep.append({'timestamp': row_data['timestamp'], 'price': row_data['price']})
        
        if not rows_to_keep:
            print("No data to keep after processing for cleanup.") # Placeholder for better logging
            return

        reduced_df = pd.DataFrame(rows_to_keep)

        cursor = conn.cursor()
        cursor.execute("DELETE FROM prices")
        reduced_df.to_sql('prices', conn, if_exists='append', index=False, method='multi', chunksize=100) # Added method and chunksize
        conn.commit()
        print(f"Price history cleaned. Original: {len(df_all_history)}, Reduced: {len(reduced_df)}") # Placeholder

    except sqlite3.Error as e:
        print(f"SQLite error during history cleanup: {e}") # Placeholder
        if conn: conn.rollback()
    except Exception as e:
        print(f"General error during history cleanup: {e}") # Placeholder
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

def get_price_stats() -> dict:
    """Calculate statistics (total entries, min, max, average price) from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT price FROM prices")
        prices = [row[0] for row in cursor.fetchall() if row[0] is not None]

        if not prices:
            return {"total_entries": 0, "min_price": None, "max_price": None, "average_price": None}
        
        return {
            "total_entries": len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "average_price": round(sum(prices) / len(prices), 2) if prices else None
        }
    except sqlite3.Error as e:
        print(f"Database error calculating stats: {str(e)}") # Placeholder
        return {"error": str(e)} # Or raise an exception
    finally:
        conn.close()