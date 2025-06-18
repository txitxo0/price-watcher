from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any

class BasePriceCRUD(ABC):
    @abstractmethod
    def init_db(self) -> None:
        """Initializes the database schema if required."""
        pass

    @abstractmethod
    def save_price_entry(self, price_value: float) -> None:
        """Saves a single price entry."""
        pass

    @abstractmethod
    def get_all_price_entries_df(self) -> pd.DataFrame:
        """Retrieves all price entries as a Pandas DataFrame.
           The DataFrame should have 'date' (timestamp) and 'price' columns.
        """
        pass

    @abstractmethod
    def get_latest_price_entry(self) -> Optional[Tuple[str, float]]:
        """Retrieves the latest price entry (timestamp, price)."""
        pass

    @abstractmethod
    def delete_all_prices(self) -> None:
        """Deletes all price entries."""
        pass

    @abstractmethod
    def bulk_insert_prices(self, price_entries: List[Dict[str, Any]]) -> None:
        """Bulk inserts price entries. Each dict should have 'timestamp' and 'price'."""
        pass

    @abstractmethod
    def get_price_stats(self) -> Dict[str, Any]:
        """Calculates and returns price statistics.
           Expected keys: 'total_entries', 'min_price', 'max_price', 'average_price'.
        """
        pass