from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from app.services import price_service, reporting_service
from app.core.config import settings
from app.utils.logging_utils import log_message # For logging API errors if needed

# Renamed 'app' to 'app_router' to avoid conflict with FastAPI instance in main.py
app_router = APIRouter(prefix="/api")


@app_router.get("/health")
def health_check():
    """
    Health check endpoint to verify if the server is running.
    
    Returns:
        JSON object with a 'status' key indicating the server status.
    """
    return {"status": "ok", "message": "Price Watcher API is running."}

@app_router.get("/history/text")
def get_history_text():
    """
    Fetch the historical price data in CSV format and return related statistics.
    
    Reads a CSV file containing historical price data, returns it as a JSON object, 
    and includes the statistics (total entries, min, max, and average price).

    Returns:
        JSON object with 'data' containing the historical price records and 'metadata'
        containing statistics such as total entries, min price, max price, and average price.
    
    Raises:
        HTTPException: If the file is not found, a 404 error is returned.
    """
    try:
        df_history = price_service.get_all_prices_df()
        # Convert DataFrame to list of dicts, 'date' column from df is used as 'timestamp'
        data = df_history.rename(columns={'date': 'timestamp'}).to_dict(orient='records')
        
        stats = price_service.get_price_statistics()

        return {
            "data": data,
            "metadata": stats
        }
    except Exception as e:
        log_message(f"API Error in /history/text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app_router.get("/history/image")
def get_history_image():
    """
    Retrieve the price history image (PNG).
    
    Returns the PNG image that visualizes the historical price data.

    Returns:
        FileResponse: The image file as a response with the correct MIME type.

    Raises:
        HTTPException: If the image is not found, a 404 error is returned.
    """
    try:
        image_path = reporting_service.generate_price_history_graph() # Ensures latest graph
        if image_path and os.path.exists(image_path):
            return FileResponse(image_path, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail=f"Image not found or could not be generated.")
    except Exception as e:
        log_message(f"API Error in /history/image: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving image: {str(e)}")

@app_router.get("/latest-price")
def get_latest_price():
    """
    Retrieve the latest recorded price.

    Returns:
        JSON object with 'timestamp' and 'latest_price' keys.

    Raises:
        HTTPException: If there is an error reading the database or no data is found.
    """
    try:
        latest_entry = price_service.get_latest_price()
        if not latest_entry:
            raise HTTPException(status_code=404, detail="No price data found in database.")
        return {"timestamp": latest_entry[0], "latest_price": latest_entry[1]}
    except HTTPException: # Re-raise HTTP exceptions from db module if any
        raise
    except Exception as e:
        log_message(f"API Error in /latest-price: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving latest price: {str(e)}")

@app_router.get("/stats")
def get_stats():
    """
    Calculate and return statistics on the historical prices.
    
    Computes the total number of price entries, the minimum, maximum, and average price from the history.

    Returns:
        JSON object containing 'total_entries', 'min_price', 'max_price', and 'average_price'.

    Raises:
        HTTPException: If there is an error reading the file or calculating statistics, a 500 error is returned.
    """
    try:
        return price_service.get_price_statistics()
    except HTTPException: # Re-raise HTTP exceptions from get_stats_data_from_db
        raise
    except Exception as e: # Catch other potential errors
        log_message(f"API Error in /stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")

@app_router.post("/trigger")
def trigger_iteration():
    """
    Manually trigger a new price iteration.
    
    Executes the `trigger_new_price_iteration` function to start a new iteration for updating prices.

    Returns:
        JSON object with a confirmation message that the manual trigger was executed.
    """
    try:
        price_service.process_new_price_iteration()
        return {"message": "Manual price check iteration triggered successfully."}
    except Exception as e:
        log_message(f"API Error in /trigger: {e}")
        raise HTTPException(status_code=500, detail=f"Error triggering iteration: {str(e)}")
