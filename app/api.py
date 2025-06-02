from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from . import database_manager as db # Use relative import for intra-package module
from .price_watcher import trigger_new_price_iteration # Use relative import


HISTORY_IMAGE_PATH = "./data/price_history.png"
app = FastAPI()
router = APIRouter(prefix="/api")


@router.get("/health")
def health_check():
    """
    Health check endpoint to verify if the server is running.
    
    Returns:
        JSON object with a 'status' key indicating the server status.
    """
    return {"status": "ok"}

@router.get("/history/text")
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
        df_history = db.load_all_price_history_df()
        # Convert DataFrame to list of dicts, 'date' column from df is used as 'timestamp'
        data = df_history.rename(columns={'date': 'timestamp'}).to_dict(orient='records')
        
        stats = db.get_price_stats()

        return {
            "data": data,
            "metadata": stats
        }
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/image")
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
        if os.path.exists(HISTORY_IMAGE_PATH):
            return FileResponse(HISTORY_IMAGE_PATH, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail=f"Image not found at {HISTORY_IMAGE_PATH}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest-price")
def get_latest_price():
    """
    Retrieve the latest recorded price.

    Returns:
        JSON object with 'timestamp' and 'latest_price' keys.

    Raises:
        HTTPException: If there is an error reading the database or no data is found.
    """
    try:
        latest_entry = db.get_latest_price_entry()
        if not latest_entry:
            raise HTTPException(status_code=404, detail="No price data found in database.")
        return {"timestamp": latest_entry[0], "latest_price": latest_entry[1]}
    except HTTPException: # Re-raise HTTP exceptions from db module if any
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
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
        return db.get_price_stats()
    except HTTPException: # Re-raise HTTP exceptions from get_stats_data_from_db
        raise
    except Exception as e: # Catch other potential errors
        raise HTTPException(status_code=500, detail=f"Error calculating stats: {str(e)}")

@router.post("/trigger")
def trigger_iteration():
    """
    Manually trigger a new price iteration.
    
    Executes the `trigger_new_price_iteration` function to start a new iteration for updating prices.

    Returns:
        JSON object with a confirmation message that the manual trigger was executed.
    """
    trigger_new_price_iteration()
    return {"message": "Manual trigger executed"}


app.include_router(router)
# uvicorn api:app --reload
