import asyncio
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import os
import pandas as pd
import requests
import time
from . import database_manager as db # Use relative import for intra-package module


LOG_FILE = "./data/price_watcher.log"
MAX_LOG_SIZE = 1_048_576  # 1 MB
HISTORY_IMAGE_PATH = "./data/price_history.png"
URL= os.environ.get("URL")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DELAY_SECONDS = int(os.environ.get("DELAY_SECONDS", 60))

def log_message(message):
    """Save message in log file"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    #Rotate log
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
        open(LOG_FILE, "w").close()

    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")


def send_telegram_message(message, graph_filename=None):
    """Send Telegram message and, optionally, a graphic image."""
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    
    params = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        log_message(f"Error sending Telegram message: {response.text}")
    
    if graph_filename:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto'
        with open(graph_filename, 'rb') as photo:
            files = {'photo': photo}
            params = {'chat_id': TELEGRAM_CHAT_ID}
            photo_response = requests.post(url, params=params, files=files)
        
        if photo_response.status_code != 200:
            log_message(f"Error sending image to Telegram: {photo_response.text}")
        else:
            log_message("Image sent successfully to Telegram.")
    else:
        print("Notification sended sucessfully")

def get_product_info(price_selector, name_selector):
    """Get price and product name."""
    log_message(f"Getting info from {URL}...")
    try:
        response = requests.get(URL, timeout=10) # Added timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        log_message(f"Error getting webpage: {e}")
        return None, None
    
    # if response.status_code != 200: # Covered by raise_for_status
    #     log_message(f"Error getting webpage: {response.status_code}")
    #     return None, None

    soup = BeautifulSoup(response.text, "html.parser")
    
    price_element = soup.select(price_selector)

    if not price_element:
        log_message("Price element not found.")
        price = None
    else:
        # Attempt to extract price, more robustly
        raw_price = price_element[0].text.strip()
        # Remove currency symbols and whitespace, then replace comma with dot for float conversion
        cleaned_price = ''.join(filter(lambda x: x.isdigit() or x == '.' or x == ',', raw_price))
        price = cleaned_price.replace(",", ".")

    product_name_element = soup.select(name_selector)
    if not product_name_element:
        log_message("Product name not found.")
        product_name = None
    else:
        product_name = product_name_element[0].text.strip()

    if product_name and price:
        try:
            float_price = float(price)
            log_message(f"Product: {product_name}, Price: {float_price}€")
            return product_name, float_price
        except ValueError:
            log_message(f"Could not convert price '{price}' to float for product '{product_name}'.")
            return product_name, None
    else:
        log_message(f"Product name or price could not be extracted. Name: '{product_name}', Raw Price: '{price}'")
        return product_name, None

def generate_price_graph():
    """Render graphic image of the historical prices."""
    df = db.load_all_price_history_df()
    if df.empty:
        log_message("There is no data to create an image.")
        return None
    
    plt.figure()
    plt.plot(pd.to_datetime(df['date']), df['price'], marker='o')
    plt.title('Price evolution')
    plt.xlabel('Date')
    plt.ylabel('Price (€)')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(HISTORY_IMAGE_PATH), exist_ok=True)
    plt.savefig(HISTORY_IMAGE_PATH)
    plt.close() # Close the plot to free memory
    log_message(f"Image rendered: {HISTORY_IMAGE_PATH}")
    return HISTORY_IMAGE_PATH

def trigger_new_price_iteration():
    try:
        # Get current price
        price_selector = os.getenv('PRODUCT_PRICE_SELECTOR', 'span.money[data-price="true"]')
        name_selector = os.getenv('PRODUCT_NAME_SELECTOR', 'h2.product-title')
        product_name, current_price = get_product_info(price_selector, name_selector )

        if current_price:
            # Save current price in the history
            latest_entry = db.get_latest_price_entry()
            previous_latest_price = latest_entry[1] if latest_entry else None
            # save_price_history(current_price)
            db.save_price_entry(current_price)
            graph_filename = generate_price_graph()
            # Check if price dropped compared to the previous latest price
            if previous_latest_price is not None and current_price < previous_latest_price:
                discount_percentage = ((previous_latest_price - current_price) / previous_latest_price) * 100
                message = f"¡Alerta! El precio de {product_name} ha bajado.\n\n" \
                          f"Precio anterior: {previous_latest_price}€\n" \
                          f"Precio actual: {current_price}€\n" \
                          f"Descuento: {discount_percentage:.2f}%\n" \
                          f"Url: {URL}"
                log_message(f"Price drop! {previous_latest_price}€ → {current_price}€ for {product_name}")
                if graph_filename:
                    message = f"¡Alerta! El precio de {product_name} ha bajado.\n\n"
                    send_telegram_message(message, graph_filename)
                else:
                    send_telegram_message(message)
            elif previous_latest_price is not None and current_price == previous_latest_price:
                log_message(f"Price for {product_name} is {current_price}€. Previous: {previous_latest_price if previous_latest_price is not None else 'N/A'}") 
            elif previous_latest_price is not None and current_price > previous_latest_price:
                log_message(f"Price for {product_name} increased to {current_price}€. Previous: {previous_latest_price}")
    #             else:
    #                 log_message(f"The price stays: {current_price}€")
    #     else:
    #         log_message("Price could not be obtained.")
    # except Exception as e:
    #     log_message(f"Error: {str(e)}")
    #     log_message(f"Waiting {DELAY_SECONDS} seconds to the next iteration...")
    except Exception as e:
        log_message(f"Error in trigger_new_price_iteration: {str(e)}")

async def watch_prices():
    # Ensure log directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    # Initialize database (which also handles its directory creation)
    db.init_db()
    log_message("Price watcher started.")
    iteration = 1
    while True:
        log_message(f"Starting iteration {iteration}...")
        trigger_new_price_iteration()
        
        # Clean history approximately once a day
        # Assumes DELAY_SECONDS is in seconds.
        # (24 hours * 60 minutes * 60 seconds) / DELAY_SECONDS = iterations per day
        iterations_per_day = (24 * 60 * 60) / DELAY_SECONDS if DELAY_SECONDS > 0 else 1440 # Default to 1440 if DELAY_SECONDS is 0 or invalid
        
        if iteration % int(iterations_per_day) == 0 and iteration != 0: # Clean once per day, avoid cleaning at iteration 0
            log_message("Attempting to clean price history...")
            db.clean_price_history_db()
            # Optionally reset iteration if you want the count to restart after cleaning,
            # or let it continue to grow. If resetting: iteration = 0
        iteration += 1
        await asyncio.sleep(DELAY_SECONDS)
