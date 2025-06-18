import os
import time
from app.core.config import settings

def log_message(message: str):
    """Save message in log file with rotation."""
    log_dir = os.path.dirname(settings.LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)

    # Rotate log
    if os.path.exists(settings.LOG_FILE) and os.path.getsize(settings.LOG_FILE) > settings.MAX_LOG_SIZE:
        open(settings.LOG_FILE, "w").close() # Simple rotation: clear file

    with open(settings.LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")