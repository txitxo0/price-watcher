from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import os
import pandas as pd
import requests
import time

LOG_FILE = "./data/price_watcher.log"
HISTORY_FILE = "./data/prices.csv"
URL= os.environ.get("URL")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DELAY_SECONDS = int(os.environ.get("DELAY_SECONDS", 60))

def log_message(message):
    """Save message in log file"""
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
        print(f"Send notification: {response.text}")
    
    if graph_filename:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto'
        with open(graph_filename, 'rb') as photo:
            files = {'photo': photo}
            params = {'chat_id': TELEGRAM_CHAT_ID}
            response = requests.post(url, params=params, files=files)
        
        if response.status_code != 200:
            print(f"Error sending image: {response.text}")
        else:
            print("Image sended sucessfully")
    else:
        print("Notification sended sucessfully")

def get_product_info(price_selector, name_selector):
    """Get price and product name."""
    log_message(f"Getting info from {URL}...")
    response = requests.get(URL)
    
    if response.status_code != 200:
        log_message(f"Error getting webpage: {response.status_code}")
        return None, None

    soup = BeautifulSoup(response.text, "html.parser")
    
    price_element = soup.select(price_selector)

    if not price_element:
        log_message("Price element not found.")
        price = None
    else:
        price = price_element[0].text.strip().replace("€", "").replace(",", ".")

    product_name_element = soup.select(name_selector)
    if not product_name_element:
        log_message("Product name not found.")
        product_name = None
    else:
        product_name = product_name_element[0].text.strip()

    log_message(f"Product: {product_name}, Price: {price}€")
    return product_name, float(price) if price else None


def load_price_history():
    """Load history prices from the CSV file."""
    try:
        df = pd.read_csv(HISTORY_FILE)
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["date", "price"])


def save_price_history(price):
    """Save new prince in the CSV file."""
    df = load_price_history()
    new_row = pd.DataFrame({"date": [time.strftime('%Y-%m-%d %H:%M:%S')], "price": [price]})
    df = pd.concat([df, new_row], ignore_index=True) 
    df.to_csv(HISTORY_FILE, index=False)


def generate_price_graph():
    """Render graphic image of the historical prices."""
    df = load_price_history()
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
    
    graph_filename = './data/price_history.png'
    plt.savefig(graph_filename)
    log_message(f"Image rendered: {graph_filename}")
    return graph_filename


def check_price_drop(current_price):
    """Chech price drop."""
    df = load_price_history()
    if df.empty:
        return False
    if len(df) > 1:
        last_price = df.iloc[-1]["price"]
    else:
        last_price = current_price
    if current_price < last_price:
        log_message(f"Price drop! {last_price}€ → {current_price}€")
        return True
    return False


os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
while True:
    try:
        # Get current price
        price_selector = os.getenv('PRODUCT_PRICE_SELECTOR', 'span.money[data-price="true"]')
        name_selector = os.getenv('PRODUCT_NAME_SELECTOR', 'h2.product-title')
        product_name, current_price = get_product_info(price_selector, name_selector )

        if current_price:
            # Save current price in the history
            save_price_history(current_price)
            
            # Check if price drop
            df = load_price_history() 
            if df.empty:
                log_message("There is no data to compare.")
            else:
                if len(df) > 1:
                    last_price = df.iloc[-2]["price"]
                else:
                    last_price = current_price

                if check_price_drop(current_price):
                    graph_filename = generate_price_graph()
                    
                    discount_percentage = ((last_price - current_price) / last_price) * 100
                    message = f"¡Alerta! El precio de {product_name} ha bajado.\n\n" \
                            f"Precio anterior: {last_price}€\n" \
                            f"Precio actual: {current_price}€\n" \
                            f"Descuento: {discount_percentage:.2f}%\n" \
                            f"Url: {URL}"
                    
                    if graph_filename:
                        send_telegram_message(message, graph_filename)
                    else:
                        send_telegram_message(message)
                else:
                    log_message(f"The price stays: {current_price}€")
        else:
            log_message("Price could not be obtained.")
    except Exception as e:
        log_message(f"Error: {str(e)}")
        log_message(f"Waiting {DELAY_SECONDS} seconds to the next iteration...")
    time.sleep(DELAY_SECONDS)