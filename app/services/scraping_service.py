import requests
from bs4 import BeautifulSoup
# from app.core.config import settings # No longer needed for product-specific details
from app.utils.logging_utils import log_message

def get_product_info(url: str, price_selector: str, name_selector: str) -> tuple[str | None, float | None]:
    """
    Get price and product name from the given URL using provided CSS selectors.
    Returns (product_name, price).
    """
    log_message(f"Getting info from {url}...")
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'PriceWatcher/1.0'})
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        log_message(f"Error getting webpage: {e}")
        return None, None

    soup = BeautifulSoup(response.text, "html.parser")
    
    price_element = soup.select(price_selector)
    price_str = None
    if price_element:
        raw_price = price_element[0].text.strip()
        cleaned_price = ''.join(filter(lambda x: x.isdigit() or x == '.' or x == ',', raw_price))
        price_str = cleaned_price.replace(",", ".")

    product_name_element = soup.select(name_selector)
    product_name = product_name_element[0].text.strip() if product_name_element else None

    if not product_name:
        log_message("Product name not found.")
    if not price_str:
        log_message("Price element not found or price could not be extracted.")

    if product_name and price_str:
        try:
            float_price = float(price_str)
            log_message(f"Product: {product_name}, Price: {float_price}€")
            return product_name, float_price
        except ValueError:
            log_message(f"Could not convert price '{price_str}' to float for product '{product_name}'.")
            return product_name, None
    return product_name, None