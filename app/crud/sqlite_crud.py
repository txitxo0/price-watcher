import sqlite3
import pandas as pd
import os
from datetime import datetime
from app.utils.logging_utils import log_message
from .base import BasePriceCRUD, BaseProductCRUD
from app.schemas.product import ProductCreate, ProductUpdate, generate_slug
from typing import List, Dict, Tuple, Optional, Any

class SQLitePriceCRUD(BasePriceCRUD):
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self) -> None:
        """Initializes the prices table. Product table initialization is separate."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_product_id_timestamp ON prices (product_id, timestamp);")
        conn.commit()
        conn.close()

    def save_price_entry(self, product_id: int, price_value: float) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            cursor.execute("INSERT INTO prices (product_id, timestamp, price) VALUES (?, ?, ?)",
                           (product_id, current_timestamp, price_value))
            conn.commit()
            log_message(f"Saved price {price_value} for product_id {product_id}")
        except sqlite3.Error as e:
            log_message(f"SQLite Error saving price: {e}")
        finally:
            conn.close()

    def get_all_price_entries_df(self, product_id: int) -> pd.DataFrame:
        conn = self._get_connection()
        # This method needs product_id, so the signature in base and here must match.
        # For now, let's assume it's called with a product_id if used.
        # The original call in endpoints.py needs to be updated or this method needs to be product_id specific.
        # Let's make it product_id specific as per the base class.
        try:
            df = pd.read_sql_query("SELECT timestamp as date, price FROM prices WHERE product_id = ? ORDER BY timestamp ASC", conn, params=(product_id,))
        except (pd.io.sql.DatabaseError, sqlite3.Error) as e:
            log_message(f"SQLite Error loading price history to DataFrame: {e}")
            df = pd.DataFrame(columns=["date", "price"])
        finally:
            conn.close()
        return df

    def get_latest_price_entry(self, product_id: int) -> Optional[Tuple[str, float]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT timestamp, price FROM prices WHERE product_id = ? ORDER BY id DESC LIMIT 1", (product_id,))
            row = cursor.fetchone()
            return row if row else None
        except sqlite3.Error as e:
            log_message(f"SQLite Error fetching latest price for product_id {product_id}: {e}")
            return None
        finally:
            conn.close()

    def delete_prices_for_product(self, product_id: int) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM prices WHERE product_id = ?", (product_id,))
            conn.commit()
            log_message(f"All price entries for product_id {product_id} deleted from SQLite.")
        except sqlite3.Error as e:
            log_message(f"SQLite Error deleting prices for product_id {product_id}: {e}")
            conn.rollback()
        finally:
            conn.close()

    def bulk_insert_prices_for_product(self, product_id: int, price_entries: List[Dict[str, Any]]) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            data_to_insert = [(product_id, entry['timestamp'], entry['price']) for entry in price_entries]
            cursor.executemany("INSERT INTO prices (product_id, timestamp, price) VALUES (?, ?, ?)", data_to_insert)
            conn.commit()
            log_message(f"Bulk inserted {len(data_to_insert)} price entries for product_id {product_id} into SQLite.")
        except sqlite3.Error as e:
            log_message(f"SQLite Error bulk inserting prices for product_id {product_id}: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_price_stats(self, product_id: int) -> Dict[str, Any]:
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
                WHERE price IS NOT NULL AND product_id = ?
            """, (product_id,))

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
            log_message(f"SQLite Database error calculating stats for product_id {product_id}: {str(e)}")
            # Consider re-raising a custom DB error or returning a default error structure
            raise # Re-raise to be handled by service/API layer
        finally:
            conn.close()


class SQLiteProductCRUD(BaseProductCRUD):
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row # To access columns by name
        conn.execute("PRAGMA foreign_keys = ON;") # Ensure foreign key constraints are enforced
        return conn

    def init_db(self) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL UNIQUE,
                price_selector TEXT NOT NULL,
                name_selector TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TEXT NOT NULL,
                last_checked_at TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_slug ON products (slug);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_is_active ON products (is_active);")
        conn.commit()
        conn.close()

    def create_product(self, product: ProductCreate) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        final_slug = product.slug or generate_slug(product.name)

        try:
            cursor.execute("""
                INSERT INTO products (name, slug, url, price_selector, name_selector, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (product.name, final_slug, str(product.url), product.price_selector,
                  product.name_selector, product.is_active, current_time))
            conn.commit()
            product_id = cursor.lastrowid
            return self.get_product_by_id(product_id)
        except sqlite3.IntegrityError as e: # Handles UNIQUE constraint violations for slug or URL
            log_message(f"SQLite IntegrityError creating product (slug/url likely exists): {e} - Slug: {final_slug}, URL: {product.url}")
            return None
        except sqlite3.Error as e:
            log_message(f"SQLite Error creating product: {e}")
            return None
        finally:
            conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> Optional[Dict[str, Any]]:
        return dict(row) if row else None

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_dict(row)

    def get_product_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE slug = ?", (slug,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_dict(row)

    def get_product_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE url = ?", (url,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_dict(row)

    def get_all_products(self, skip: int = 0, limit: int = 100, active_only: bool = False) -> Tuple[List[Dict[str, Any]], int]:
        conn = self._get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM products"
        count_query = "SELECT COUNT(*) FROM products"
        params = []
        if active_only:
            query += " WHERE is_active = TRUE"
            count_query += " WHERE is_active = TRUE"

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, skip])

        cursor.execute(query, params)
        products = [self._row_to_dict(row) for row in cursor.fetchall()]

        cursor.execute(count_query)
        total_count = cursor.fetchone()[0]

        conn.close()
        return products, total_count

    def update_product(self, product_id: int, product_update: ProductUpdate) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        fields_to_update = {k: v for k, v in product_update.model_dump(exclude_unset=True).items() if v is not None}
        if not fields_to_update:
            return self.get_product_by_id(product_id) # No changes

        set_clause = ", ".join([f"{field} = ?" for field in fields_to_update.keys()])
        values = list(fields_to_update.values())
        values.append(product_id)

        try:
            cursor.execute(f"UPDATE products SET {set_clause} WHERE id = ?", tuple(values))
            conn.commit()
            return self.get_product_by_id(product_id) if cursor.rowcount > 0 else None
        except sqlite3.IntegrityError as e: # Handles UNIQUE constraint violations for slug or URL
            log_message(f"SQLite IntegrityError updating product (slug/url likely exists for another product): {e}")
            return None
        except sqlite3.Error as e:
            log_message(f"SQLite Error updating product {product_id}: {e}")
            return None
        finally:
            conn.close()

    def delete_product(self, product_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Foreign key ON DELETE CASCADE should handle prices table entries
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            log_message(f"SQLite Error deleting product {product_id}: {e}")
            return False
        finally:
            conn.close()

    def update_last_checked_at(self, product_id: int) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE products SET last_checked_at = ? WHERE id = ?",
                           (datetime.now().isoformat(), product_id))
            conn.commit()
        except sqlite3.Error as e:
            log_message(f"SQLite Error updating last_checked_at for product {product_id}: {e}")
        finally:
            conn.close()