import os
from dotenv import load_dotenv

# Load .env file from the project root (one level up from app/core)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings:
    # PRODUCT_URL: str = os.getenv("URL", "") # Removed
    # PRODUCT_PRICE_SELECTOR: str = os.getenv("PRODUCT_PRICE_SELECTOR", "span.money[data-price]") # Removed
    # PRODUCT_NAME_SELECTOR: str = os.getenv("PRODUCT_NAME_SELECTOR", "h2.product-title") # Removed
    TELEGRAM_TOKEN: str | None = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID: str | None = os.getenv("TELEGRAM_CHAT_ID")
    DELAY_SECONDS: int = int(os.getenv("DELAY_SECONDS", "60"))
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite")

    # Database connection details (primarily for non-SQLite DBs)
    DB_HOST: str | None = os.getenv("DB_HOST")
    DB_PORT: int | None = int(os.getenv("DB_PORT")) if os.getenv("DB_PORT") else None
    DB_USER: str | None = os.getenv("DB_USER")
    DB_PASSWORD: str | None = os.getenv("DB_PASSWORD")
    DB_NAME: str | None = os.getenv("DB_NAME")

    DB_FILE: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "price_watcher.db")
    LOG_FILE: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "price_watcher.log")
    HISTORY_IMAGE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "graphs") # Directory for graphs
    # HISTORY_IMAGE_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "price_history.png") # Removed, will be dynamic
    MAX_LOG_SIZE: int = 1_048_576  # 1 MB
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

settings = Settings()