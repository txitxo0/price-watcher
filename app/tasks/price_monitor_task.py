import asyncio
from app.core.config import settings
from app.services import price_service
from app.utils.logging_utils import log_message
# No direct CRUD import needed here if init_db is handled by main and services use the handler

async def watch_prices_task():
    """Main async task to periodically check prices and perform maintenance."""
    log_message("Price watcher task started.")
    # Initialization is handled in main.py via price_crud_handler

    iteration = 0
    while True:
        iteration += 1
        log_message(f"Price monitor task: Starting iteration {iteration}...")
        
        try:
            price_service.process_new_price_iteration()

            # Clean history approximately once a day
            iterations_per_day = (24 * 60 * 60) / settings.DELAY_SECONDS if settings.DELAY_SECONDS > 0 else 1440
            if iteration % int(iterations_per_day) == 0:
                price_service.clean_price_history()
        except Exception as e:
            log_message(f"Error in watch_prices_task main loop: {e}")
            # Add more robust error handling or backoff if needed

        await asyncio.sleep(settings.DELAY_SECONDS)
