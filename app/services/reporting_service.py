import matplotlib
matplotlib.use('Agg') # Set the backend before importing pyplot
import matplotlib.pyplot as plt
import pandas as pd
import os
from app.core.config import settings
from app.crud import price_crud_handler # Use the abstracted handler
from app.utils.logging_utils import log_message



def generate_price_history_graph() -> str | None:
    """Generate a graph of price history and save it. Returns the path to the image or None."""
    df = price_crud_handler.get_all_price_entries_df()
    if df.empty:
        log_message("No data to generate price history graph.")
        return None

    plt.figure(figsize=(10, 6))
    plt.plot(pd.to_datetime(df['date']), df['price'], marker='o', linestyle='-')
    plt.title('Price Evolution')
    plt.xlabel('Date')
    plt.ylabel('Price (€)')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(settings.HISTORY_IMAGE_PATH), exist_ok=True)
    plt.savefig(settings.HISTORY_IMAGE_PATH)
    plt.close() # Close the plot to free memory
    log_message(f"Price history graph generated: {settings.HISTORY_IMAGE_PATH}")
    return settings.HISTORY_IMAGE_PATH