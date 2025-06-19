from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import FileResponse, JSONResponse
import os
from app.services import price_service, reporting_service
from app.core.config import settings
from app.utils.logging_utils import log_message # For logging API errors if needed
from app.schemas.product import Product, ProductCreate, ProductUpdate, ProductList
from app.crud import product_crud_handler, price_crud_handler # Import both handlers
from typing import List, Union

# Renamed 'app' to 'app_router' to avoid conflict with FastAPI instance in main.py
app_router = APIRouter(prefix="/api")

# --- Helper function to get product or raise 404 ---
def get_product_or_404(product_id_or_slug: Union[int, str]):
    if isinstance(product_id_or_slug, int):
        db_product = product_crud_handler.get_product_by_id(product_id_or_slug)
    else:
        db_product = product_crud_handler.get_product_by_slug(product_id_or_slug)
    if not db_product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id_or_slug}' not found")
    return Product(**db_product)

@app_router.get("/health")
def health_check():
    """
    Health check endpoint to verify if the server is running.
    
    Returns:
        JSON object with a 'status' key indicating the server status.
    """
    return {"status": "ok", "message": "Price Watcher API is running."}

# --- Product CRUD Endpoints ---

@app_router.post("/products/", response_model=Product, status_code=201)
def create_product_endpoint(product: ProductCreate):
    """
    Create a new product to track.
    The `slug` will be auto-generated from the name if not provided.
    URL and slug must be unique.
    """
    # Check if URL or slug already exists to provide a more specific error
    if product_crud_handler.get_product_by_url(str(product.url)):
        raise HTTPException(status_code=409, detail=f"Product with URL '{product.url}' already exists.")
    
    # Slug is generated/validated by Pydantic model, but check DB for existing slug
    final_slug = product.slug # Pydantic model ensures this is set
    if product_crud_handler.get_product_by_slug(final_slug):
        raise HTTPException(status_code=409, detail=f"Product with slug '{final_slug}' already exists. Try a different name or provide a unique slug.")

    created_product_dict = product_crud_handler.create_product(product)
    if not created_product_dict:
        # This might happen if there's a race condition or other DB error not caught by pre-checks
        raise HTTPException(status_code=500, detail="Failed to create product due to a database error or conflict.")
    return Product(**created_product_dict)

@app_router.get("/products/", response_model=ProductList)
def list_products_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    active_only: bool = Query(False)
):
    """
    List all tracked products with pagination.
    """
    products_list, total_count = product_crud_handler.get_all_products(skip=skip, limit=limit, active_only=active_only)
    return ProductList(products=[Product(**p) for p in products_list], total=total_count)

@app_router.get("/products/{product_id_or_slug}", response_model=Product)
def get_product_endpoint(product: Product = Depends(get_product_or_404)):
    """
    Get a specific product by its ID or slug.
    """
    return product

@app_router.put("/products/{product_id_or_slug}", response_model=Product)
def update_product_endpoint(product_update: ProductUpdate, product_db: Product = Depends(get_product_or_404)):
    """
    Update a product's details by its ID or slug.
    Only provided fields will be updated.
    """
    updated_product_dict = product_crud_handler.update_product(product_id=product_db.id, product_update=product_update)
    if not updated_product_dict:
        raise HTTPException(status_code=409, detail="Failed to update product, possibly due to a slug/URL conflict or product not found after update.")
    return Product(**updated_product_dict)

@app_router.delete("/products/{product_id_or_slug}", status_code=204)
def delete_product_endpoint(product_db: Product = Depends(get_product_or_404)):
    """
    Delete a product by its ID or slug. This will also delete its associated price history.
    """
    if not product_crud_handler.delete_product(product_id=product_db.id):
        # Should not happen if get_product_or_404 worked, but as a safeguard
        raise HTTPException(status_code=500, detail="Failed to delete product.")
    return None # FastAPI handles 204 No Content response


# --- Existing Endpoints (to be modified for multi-product) ---

@app_router.get("/products/{product_id_or_slug}/history/text")
def get_history_text(product: Product = Depends(get_product_or_404)):
    """
    Fetch the historical price data in CSV format and return related statistics.
    for a specific product.

    Returns:
        JSON object with 'data' containing the historical price records and 'metadata'
        containing statistics such as total entries, min price, max price, and average price.
    
    Raises:
        HTTPException: If the file is not found, a 404 error is returned.
    """
    try:
        df_history = price_service.get_all_prices_df(product_id=product.id)
        # Convert DataFrame to list of dicts, 'date' column from df is used as 'timestamp'
        data = df_history.rename(columns={'date': 'timestamp'}).to_dict(orient='records')
        
        stats = price_service.get_price_statistics(product_id=product.id)

        return {
            "data": data,
            "metadata": stats
        }
    except Exception as e:
        log_message(f"API Error in /products/{product.slug}/history/text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app_router.get("/products/{product_id_or_slug}/history/image")
def get_history_image(product: Product = Depends(get_product_or_404)):
    """
    Retrieve the price history image (PNG).
    
    Returns the PNG image that visualizes the historical price data.

    Returns:
        FileResponse: The image file as a response with the correct MIME type.

    Raises:
        HTTPException: If the image is not found, a 404 error is returned.
    """
    try:
        image_path = reporting_service.generate_price_history_graph(product_id=product.id, product_name=product.name, product_slug=product.slug)
        if image_path and os.path.exists(image_path):
            return FileResponse(image_path, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail=f"Image not found or could not be generated.")
    except Exception as e:
        log_message(f"API Error in /products/{product.slug}/history/image: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving image: {str(e)}")

@app_router.get("/products/{product_id_or_slug}/latest-price")
def get_latest_price(product: Product = Depends(get_product_or_404)):
    """
    Retrieve the latest recorded price.
    for a specific product.
    Returns:
        JSON object with 'timestamp' and 'latest_price' keys.

    Raises:
        HTTPException: If there is an error reading the database or no data is found.
    """
    try:
        latest_entry = price_service.get_latest_price(product_id=product.id)
        if not latest_entry:
            raise HTTPException(status_code=404, detail=f"No price data found for product '{product.slug}'.")
        return {"timestamp": latest_entry[0], "latest_price": latest_entry[1]}
    except HTTPException: # Re-raise HTTP exceptions from db module if any
        raise
    except Exception as e:
        log_message(f"API Error in /products/{product.slug}/latest-price: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving latest price: {str(e)}")

@app_router.get("/products/{product_id_or_slug}/stats")
def get_stats(product: Product = Depends(get_product_or_404)):
    """
    Calculate and return statistics on the historical prices.
    for a specific product.
    Computes the total number of price entries, the minimum, maximum, and average price from the history.

    Returns:
        JSON object containing 'total_entries', 'min_price', 'max_price', and 'average_price'.

    Raises:
        HTTPException: If there is an error reading the file or calculating statistics, a 500 error is returned.
    """
    try:
        return price_service.get_price_statistics(product_id=product.id)
    except HTTPException: # Re-raise HTTP exceptions from get_stats_data_from_db
        raise
    except Exception as e: # Catch other potential errors
        log_message(f"API Error in /products/{product.slug}/stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")

@app_router.post("/trigger")
def trigger_iteration(
    product_id_or_slug: Union[int, str, None] = Query(None, description="Optional product ID or slug to trigger check for a specific product. If None, all active products are checked.")
):
    """
    Manually trigger a new price iteration.
    Can optionally trigger for a specific product or for all active products.

    Returns:
        JSON object with a confirmation message that the manual trigger was executed.
    """
    try:
        target_product_id = None
        if product_id_or_slug:
            product_db = get_product_or_404(product_id_or_slug) # Validate product exists
            target_product_id = product_db.id
        price_service.process_new_price_iteration(target_product_id=target_product_id)
        message = f"Manual price check iteration triggered successfully for {'product ' + str(product_id_or_slug) if target_product_id else 'all active products'}."
        return {"message": message}
    except Exception as e:
        log_message(f"API Error in /trigger: {e}")
        raise HTTPException(status_code=500, detail=f"Error triggering iteration: {str(e)}")
