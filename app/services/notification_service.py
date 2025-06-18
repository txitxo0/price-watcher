import requests
from app.core.config import settings
from app.utils.logging_utils import log_message

def send_telegram_message(message: str, image_path: str | None = None):
    """Send Telegram message and, optionally, a graphic image."""
    if not settings.TELEGRAM_TOKEN or not settings.TELEGRAM_CHAT_ID:
        log_message("Telegram token or chat ID not configured. Skipping notification.")
        return

    url_text = f'https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage'
    params_text = {'chat_id': settings.TELEGRAM_CHAT_ID, 'text': message}
    
    try:
        response = requests.post(url_text, params=params_text, timeout=10)
        response.raise_for_status()
        log_message("Telegram message sent successfully.")
    except requests.exceptions.RequestException as e:
        log_message(f"Error sending Telegram message: {e} - {response.text if 'response' in locals() else 'No response'}")

    if image_path:
        url_photo = f'https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendPhoto'
        try:
            with open(image_path, 'rb') as photo_file:
                files = {'photo': photo_file}
                params_photo = {'chat_id': settings.TELEGRAM_CHAT_ID}
                photo_response = requests.post(url_photo, params=params_photo, files=files, timeout=20)
                photo_response.raise_for_status()
            log_message("Image sent successfully to Telegram.")
        except (requests.exceptions.RequestException, FileNotFoundError) as e:
            log_message(f"Error sending image to Telegram: {e} - {photo_response.text if 'photo_response' in locals() else 'No response'}")