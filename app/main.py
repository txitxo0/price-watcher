import asyncio
import uvicorn

from app.api.endpoints import app_router
from app.tasks.price_monitor_task import watch_prices_task
from app.core.config import settings
from app.crud import price_crud_handler # Import the handler
from fastapi import FastAPI

app = FastAPI(title="Price Watcher API")
app.include_router(app_router)

async def main():
    print(f"Starting price-watcher. API and monitor for product: {settings.PRODUCT_URL}")
    price_crud_handler.init_db() # Initialize database at startup via the handler

    config = uvicorn.Config(app, host=settings.API_HOST, port=settings.API_PORT, loop="asyncio")
    server = uvicorn.Server(config)

    watcher_task = asyncio.create_task(watch_prices_task())
    api_task = asyncio.create_task(server.serve())

    await asyncio.gather(api_task, watcher_task)

if __name__ == "__main__":
    asyncio.run(main())