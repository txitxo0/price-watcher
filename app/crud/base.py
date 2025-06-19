from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from app.schemas.product import ProductCreate, ProductUpdate # Assuming schemas are in app.schemas

class BasePriceCRUD(ABC):
    @abstractmethod
    def init_db(self) -> None:
        """Initializes the database schema if required."""
        pass

    @abstractmethod
    def save_price_entry(self, product_id: int, price_value: float) -> None:
        """Saves a single price entry."""
        pass

    @abstractmethod
    def get_all_price_entries_df(self, product_id: int) -> pd.DataFrame:
        """Retrieves all price entries as a Pandas DataFrame.
           The DataFrame should have 'date' (timestamp) and 'price' columns.
        """
        pass

    @abstractmethod
    def get_latest_price_entry(self, product_id: int) -> Optional[Tuple[str, float]]:
        """Retrieves the latest price entry (timestamp, price) for a given product."""
        pass

    @abstractmethod
    def delete_prices_for_product(self, product_id: int) -> None:
        """Deletes all price entries for a specific product."""
        pass

    @abstractmethod
    def bulk_insert_prices_for_product(self, product_id: int, price_entries: List[Dict[str, Any]]) -> None:
        """Bulk inserts price entries for a specific product. Each dict should have 'timestamp' and 'price'."""
        pass

    @abstractmethod
    def get_price_stats(self, product_id: int) -> Dict[str, Any]:
        """Calculates and returns price statistics for a given product.
           Expected keys: 'total_entries', 'min_price', 'max_price', 'average_price'.
        """
        pass

class BaseProductCRUD(ABC):
    @abstractmethod
    def init_db(self) -> None:
        """Initializes the product-related database schema if required."""
        pass

    @abstractmethod
    def create_product(self, product: ProductCreate) -> Optional[Dict[str, Any]]:
        """Creates a new product."""
        pass

    @abstractmethod
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a product by its ID."""
        pass

    @abstractmethod
    def get_product_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Retrieves a product by its slug."""
        pass

    @abstractmethod
    def get_product_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieves a product by its URL."""
        pass

    @abstractmethod
    def get_all_products(self, skip: int = 0, limit: int = 100, active_only: bool = False) -> Tuple[List[Dict[str, Any]], int]:
        """Retrieves all products, with pagination and optional active filter."""
        pass

    @abstractmethod
    def update_product(self, product_id: int, product_update: ProductUpdate) -> Optional[Dict[str, Any]]:
        """Updates an existing product."""
        pass

    @abstractmethod
    def delete_product(self, product_id: int) -> bool:
        """Deletes a product by its ID. Returns True if deletion was successful."""
        pass

    @abstractmethod
    def update_last_checked_at(self, product_id: int) -> None:
        """Updates the last_checked_at timestamp for a product."""
        pass