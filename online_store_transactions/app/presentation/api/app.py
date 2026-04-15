from fastapi import FastAPI

from app.presentation.api.routers import customers, orders, products


def create_app() -> FastAPI:
    app = FastAPI(title="Online Store Transactions", version="0.1.0")

    app.include_router(products.router)
    app.include_router(customers.router)
    app.include_router(orders.router)

    @app.get("/health", tags=["system"])
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
