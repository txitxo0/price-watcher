import csv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from price_watcher import trigger_new_price_iteration
import os


HISTORY_FILE = "./data/prices.csv"
HISTORY_IMAGE = "./data/price_history.png"
app = FastAPI()

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify if the server is running.
    
    Returns:
        JSON object with a 'status' key indicating the server status.
    """
    return {"status": "ok"}

@app.get("/history/text")
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
        with open(HISTORY_FILE, 'r') as file:
            reader = csv.DictReader(file)
            data = [row for row in reader]
        
        stats = get_stats_data()

        return {
            "data": data,
            "metadata": stats
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/image")
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
        
        if os.path.exists(HISTORY_IMAGE):
            return FileResponse(HISTORY_IMAGE, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Image not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/latest-price")
def get_latest_price():
    """
    Retrieve the latest recorded price.
    
    Reads the last entry from the historical price CSV file and returns the price value.

    Returns:
        JSON object with 'latest_price' key containing the most recent price.

    Raises:
        HTTPException: If there is an error reading the file or parsing the price, a 500 error is returned.
    """
    try:
        with open(HISTORY_FILE, 'r') as file:
            last_line = file.readlines()[-1]
            price = last_line.strip().split(',')[1]
        return {"latest_price": float(price)}
    except (FileNotFoundError, IndexError, ValueError) as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
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
        return get_stats_data()
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trigger")
def trigger_iteration():
    """
    Manually trigger a new price iteration.
    
    Executes the `trigger_new_price_iteration` function to start a new iteration for updating prices.

    Returns:
        JSON object with a confirmation message that the manual trigger was executed.
    """
    trigger_new_price_iteration()
    return {"message": "Manual trigger executed"}

def get_stats_data():
    """
    Calculate statistics (total entries, min price, max price, and average price)
    from the historical price data stored in the CSV file.

    Returns:
        A dictionary containing statistics: total entries, min price, max price, 
        and average price rounded to two decimals.

    Raises:
        ValueError: If there is an issue with reading or processing the file data.
    """
    try:
        with open(HISTORY_FILE, 'r') as file:
            reader = csv.DictReader(file)
            data = [row for row in reader]

        # Calculate the stats
        prices = [float(row['price']) for row in data]  # Assuming 'price' is a column in your CSV
        stats = {
            "total_entries": len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "average_price": round(sum(prices) / len(prices), 2)
        }
        return stats
    except Exception as e:
        raise ValueError(f"Error calculating statistics: {str(e)}")



# uvicorn api:app --reload
