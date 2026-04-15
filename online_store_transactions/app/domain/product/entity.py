from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Product:
    id: int | None
    name: str
    description: str | None
    price: Decimal
    stock_quantity: int

    def ensure_available(self, qty: int) -> None:
        if qty <= 0:
            raise ValueError("quantity must be positive")
        if self.stock_quantity < qty:
            raise ValueError(f"insufficient stock for product {self.id}")

    def decrease_stock(self, qty: int) -> None:
        self.ensure_available(qty)
        self.stock_quantity -= qty
