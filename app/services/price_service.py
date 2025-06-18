import pandas as pd
from app.crud import price_crud_handler # Use the abstracted handler
from app.services import scraping_service, notification_service, reporting_service
from app.core.config import settings
from app.utils.logging_utils import log_message

def get_price_statistics() -> dict:
    """Get price statistics from the database."""
    return price_crud_handler.get_price_stats()

def get_all_prices_df() -> pd.DataFrame:
    """Get all price entries as a DataFrame."""
    return price_crud_handler.get_all_price_entries_df()

def get_latest_price() -> tuple | None:
    """Get the latest price entry."""
    return price_crud_handler.get_latest_price_entry()

def process_new_price_iteration():
    """Fetches current price, saves it, and sends notification if price dropped."""
    log_message("Starting new price iteration process...")
    product_name, current_price = scraping_service.get_product_info()

    if current_price is None or product_name is None:
        log_message("Could not obtain product name or price. Skipping iteration.")
        return

    latest_entry_before_save = price_crud.get_latest_price_entry()
    previous_latest_price = latest_entry_before_save[1] if latest_entry_before_save else None
    
    price_crud_handler.save_price_entry(current_price)
    log_message(f"Saved current price for {product_name}: {current_price}€")
    
    graph_path = reporting_service.generate_price_history_graph()

    if previous_latest_price is not None:
        if current_price < previous_latest_price:
            discount_percentage = ((previous_latest_price - current_price) / previous_latest_price) * 100
            message = (
                f"📉 Price Drop Alert for {product_name}!\n\n"
                f"Previous Price: {previous_latest_price}€\n"
                f"Current Price: {current_price}€\n"
                f"Discount: {discount_percentage:.2f}%\n\n"
                f"Check it out: {settings.PRODUCT_URL}"
            )
            log_message(f"Price drop detected for {product_name}: {previous_latest_price}€ -> {current_price}€")
            notification_service.send_telegram_message(message, image_path=graph_path)
        elif current_price > previous_latest_price:
            log_message(f"Price increase for {product_name}: {previous_latest_price}€ -> {current_price}€")
        else:
            log_message(f"Price for {product_name} remains {current_price}€.")
    else:
        log_message(f"First price entry for {product_name}: {current_price}€")
        # Optionally send a notification for the first price entry
        # notification_service.send_telegram_message(f"Now tracking {product_name} at {current_price}€.", image_path=graph_path)

def clean_price_history():
    """Reduce database size by keeping only the first price entry for a week if prices were unchanged that week."""
    log_message("Attempting to clean price history...")
    df_all_history = price_crud_handler.get_all_price_entries_df() # 'date' column is timestamp

    if df_all_history.empty:
        log_message("Price history is empty, skipping cleanup.")
        return

    df_all_history['datetime_obj'] = pd.to_datetime(df_all_history['date'])
    df_all_history['week_num'] = df_all_history['datetime_obj'].dt.strftime('%Y-%W') # %W for week number (Monday as first day)

    rows_to_keep_df = df_all_history.groupby('week_num').apply(
        lambda g: g.iloc[0] if g['price'].nunique() == 1 else g
    ).reset_index(drop=True)

    # Prepare data for bulk insert (timestamp and price)
    rows_to_keep_list = [{'timestamp': row['date'], 'price': row['price']} for _, row in rows_to_keep_df.iterrows()]

    if rows_to_keep_list:
        price_crud_handler.delete_all_prices()
        price_crud_handler.bulk_insert_prices(rows_to_keep_list)
        log_message(f"Price history cleaned. Original: {len(df_all_history)}, Reduced: {len(rows_to_keep_df)}")
    else:
        log_message("No data to keep after processing for cleanup, or an error occurred.")