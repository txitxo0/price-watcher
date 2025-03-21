import asyncio
from api import app
from price_watcher import watch_prices
import uvicorn

async def main():
    print("Starting price-watcher. API and monitor")
    
    api_task = asyncio.create_task(uvicorn.run(app, host="0.0.0.0", port=8000))
    watcher_task = asyncio.create_task(watch_prices())
    
    await asyncio.gather(api_task, watcher_task)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
