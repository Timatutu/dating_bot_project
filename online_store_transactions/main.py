import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn
from fastapi import FastAPI

from app.routers import customers, orders, products

app = FastAPI(title="Online Store Transactions")
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(orders.router)


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
