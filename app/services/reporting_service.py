import matplotlib
matplotlib.use('Agg') # Set the backend before importing pyplot
import matplotlib.pyplot as plt
import pandas as pd
import os
from app.core.config import settings
from app.crud import price_crud_handler # Use the abstracted handler
from app.utils.logging_utils import log_message



def generate_price_history_graph(product_id: int, product_name: str, product_slug: str) -> str | None:
    """
    Generate a graph of price history for a specific product and save it.
    Returns the path to the image or None.
    """
    df = price_crud_handler.get_all_price_entries_df(product_id=product_id)
    if df.empty:
        log_message(f"No data to generate price history graph for product ID {product_id} ({product_name}).")
        return None

    plt.figure(figsize=(10, 6))
    plt.plot(pd.to_datetime(df['date']), df['price'], marker='o', linestyle='-')
    plt.title(f'Price Evolution for {product_name}')
    plt.xlabel('Date')
    plt.ylabel('Price (€)')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Ensure the directory for graphs exists
    os.makedirs(settings.HISTORY_IMAGE_DIR, exist_ok=True)
    
    # Create a unique filename for each product's graph
    image_filename = f"{product_slug}_history.png"
    image_path = os.path.join(settings.HISTORY_IMAGE_DIR, image_filename)
    
    plt.savefig(image_path)
    plt.close() # Close the plot to free memory
    log_message(f"Price history graph generated for {product_name}: {image_path}")
    return image_path