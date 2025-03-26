import asyncio
from api import app
from price_watcher import watch_prices
import uvicorn

async def main():
    print("Starting price-watcher. API and monitor")

    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)

    # Start tracker in a parallel process
    watcher_task = asyncio.create_task(watch_prices())

    # Start API REST over uvicorn
    api_task = asyncio.create_task(server.serve())

    # Run both in parallel
    await asyncio.gather(api_task, watcher_task)

if __name__ == "__main__":
    asyncio.run(main())