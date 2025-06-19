import asyncio
import uvicorn
import yaml # For YAML seeding
import os # For path joining

from app.api.endpoints import app_router
from app.tasks.price_monitor_task import watch_prices_task
from app.core.config import settings
from app.crud import price_crud_handler, product_crud_handler # Import handlers
from app.schemas.product import ProductCreate
from app.utils.logging_utils import log_message
from fastapi import FastAPI

app = FastAPI(title="Price Watcher API")
app.include_router(app_router)

def seed_products_from_yaml():
    """Loads products from products_seed.yaml and adds them if they don't exist."""
    seed_file_path = os.path.join(os.path.dirname(__file__), "products_seed.yaml") # Corrected path
    if not os.path.exists(seed_file_path):
        log_message(f"Optional product seed file '{seed_file_path}' not found. Skipping YAML seeding. Products can be managed via API.")
        return

    try:
        with open(seed_file_path, 'r') as f:
            seed_products = yaml.safe_load(f)
    except Exception as e:
        log_message(f"Error reading seed file {seed_file_path}: {e}")
        return

    if not seed_products or not isinstance(seed_products, list):
        log_message("No products found in seed file or format is incorrect.")
        return

    for prod_data in seed_products:
        try:
            product_to_create = ProductCreate(**prod_data)
            # Check if product with this URL or slug already exists
            if not product_crud_handler.get_product_by_url(str(product_to_create.url)) and \
               not product_crud_handler.get_product_by_slug(product_to_create.slug): # slug is auto-generated if None
                created = product_crud_handler.create_product(product_to_create)
                if created:
                    log_message(f"Seeded product: {created.get('name')}")
                else:
                    log_message(f"Failed to seed product (likely conflict or DB error): {product_to_create.name}")
            else:
                log_message(f"Product '{product_to_create.name}' (URL: {product_to_create.url} / Slug: {product_to_create.slug}) already exists. Skipping seed.")
        except Exception as e: # Catch Pydantic validation errors or other issues
            log_message(f"Error processing seed product data {prod_data.get('name', 'Unknown')}: {e}")

async def main():
    log_message("Starting price-watcher application...")
    product_crud_handler.init_db() # Initialize products table
    price_crud_handler.init_db()  # Initialize prices table (depends on products table for FK)
    seed_products_from_yaml()     # Seed initial products

    config = uvicorn.Config(app, host=settings.API_HOST, port=settings.API_PORT, loop="asyncio")
    server = uvicorn.Server(config)

    watcher_task = asyncio.create_task(watch_prices_task())
    api_task = asyncio.create_task(server.serve())

    await asyncio.gather(api_task, watcher_task)

if __name__ == "__main__":
    asyncio.run(main())