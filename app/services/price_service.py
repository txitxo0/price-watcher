import pandas as pd
from app.crud import price_crud_handler, product_crud_handler
from app.services import scraping_service, notification_service, reporting_service
from app.core.config import settings
from app.utils.logging_utils import log_message
from app.schemas.product import Product # For type hinting
from typing import Optional

def get_price_statistics(product_id: int) -> dict:
    """Get price statistics from the database for a specific product."""
    return price_crud_handler.get_price_stats(product_id=product_id)

def get_all_prices_df(product_id: int) -> pd.DataFrame:
    """Get all price entries as a DataFrame for a specific product."""
    return price_crud_handler.get_all_price_entries_df(product_id=product_id)

def get_latest_price(product_id: int) -> tuple | None:
    """Get the latest price entry for a specific product."""
    return price_crud_handler.get_latest_price_entry(product_id=product_id)

def _process_single_product(product_dict: dict):
    """Helper function to process price checking for a single product dictionary."""
    product = Product(**product_dict) # Convert dict to Pydantic model for easier access & type safety
    log_message(f"Processing product: {product.name} (ID: {product.id})")

    # Scrape product name from page along with price, in case it changed or for consistency
    scraped_product_name, current_price = scraping_service.get_product_info(
        url=str(product.url), # Pydantic HttpUrl needs to be cast to str for requests
        price_selector=product.price_selector,
        name_selector=product.name_selector
    )

    if current_price is None:
        log_message(f"Could not obtain price for {product.name}. Skipping this product.")
        product_crud_handler.update_last_checked_at(product.id) # Still update last_checked_at
        return

    # Use scraped name if available, otherwise fall back to DB name
    display_name = scraped_product_name if scraped_product_name else product.name

    latest_entry_before_save = price_crud_handler.get_latest_price_entry(product_id=product.id)
    previous_latest_price = latest_entry_before_save[1] if latest_entry_before_save else None
    
    price_crud_handler.save_price_entry(product_id=product.id, price_value=current_price)
    log_message(f"Saved current price for {display_name}: {current_price}€")
    
    product_crud_handler.update_last_checked_at(product.id)

    graph_path = reporting_service.generate_price_history_graph(
        product_id=product.id,
        product_name=display_name,
        product_slug=product.slug
    )

    if previous_latest_price is not None:
        if current_price < previous_latest_price:
            discount_percentage = ((previous_latest_price - current_price) / previous_latest_price) * 100
            message = (
                f"📉 Price Drop Alert for {display_name}!\n\n"
                f"Previous Price: {previous_latest_price}€\n"
                f"Current Price: {current_price}€\n"
                f"Discount: {discount_percentage:.2f}%\n\n"
                f"Check it out: {product.url}"
            )
            log_message(f"Price drop detected for {display_name}: {previous_latest_price}€ -> {current_price}€")
            notification_service.send_telegram_message(message, image_path=graph_path)
        elif current_price > previous_latest_price:
            log_message(f"Price increase for {display_name}: {previous_latest_price}€ -> {current_price}€")
        else:
            log_message(f"Price for {display_name} remains {current_price}€.")
    else:
        log_message(f"First price entry for {display_name}: {current_price}€")
        # Optionally send a notification for the first price entry
        # notification_service.send_telegram_message(f"Now tracking {display_name} at {current_price}€.", image_path=graph_path)

def process_new_price_iteration(target_product_id: Optional[int] = None):
    """
    Fetches current price for active products (or a specific product if target_product_id is provided),
    saves it, and sends notification if price dropped.
    """
    log_message("Starting new price iteration process...")
    if target_product_id:
        product_dict = product_crud_handler.get_product_by_id(target_product_id)
        if product_dict and product_dict.get('is_active'):
            products_to_check = [product_dict]
        else:
            log_message(f"Target product ID {target_product_id} not found or not active. Skipping.")
            products_to_check = []
    else:
        active_products_list, _ = product_crud_handler.get_all_products(active_only=True, limit=1000) # Assuming max 1000 active products for now
        products_to_check = active_products_list

    if not products_to_check:
        log_message("No active products to check in this iteration.")
        return

    for product_data in products_to_check:
        try:
            _process_single_product(product_data)
        except Exception as e:
            log_message(f"Error processing product ID {product_data.get('id', 'N/A')}, Name: {product_data.get('name', 'N/A')}: {e}", "ERROR")
            # Optionally, mark product as inactive or needing review after several failures

def clean_price_history():
    """Reduce database size by keeping only the first price entry for a week if prices were unchanged that week."""
    log_message("Attempting to clean price history for all products...")
    all_products, _ = product_crud_handler.get_all_products(limit=10000) # Get all products to clean history

    if not all_products:
        log_message("No products found to clean history for.")
        return

    for product_dict in all_products:
        product_id = product_dict['id']
        product_name = product_dict['name']
        log_message(f"Cleaning price history for product: {product_name} (ID: {product_id})...")
        
        df_product_history = price_crud_handler.get_all_price_entries_df(product_id=product_id)

        if df_product_history.empty:
            log_message(f"Price history for {product_name} is empty, skipping cleanup for this product.")
            continue

        df_product_history['datetime_obj'] = pd.to_datetime(df_product_history['date'])
        df_product_history['week_num'] = df_product_history['datetime_obj'].dt.strftime('%Y-%W')

        rows_to_keep_df = df_product_history.groupby('week_num').apply(
            lambda g: g.iloc[0] if g['price'].nunique() == 1 else g
        ).reset_index(drop=True)

        rows_to_keep_list = [{'timestamp': row['date'], 'price': row['price']} for _, row in rows_to_keep_df.iterrows()]

        if rows_to_keep_list:
            price_crud_handler.delete_prices_for_product(product_id=product_id)
            price_crud_handler.bulk_insert_prices_for_product(product_id=product_id, price_entries=rows_to_keep_list)
            log_message(f"Price history cleaned for {product_name}. Original: {len(df_product_history)}, Reduced: {len(rows_to_keep_df)}")
        else:
            log_message(f"No data to keep for {product_name} after processing for cleanup, or an error occurred.")