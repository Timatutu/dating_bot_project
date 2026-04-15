from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


@dataclass
class OrderItem:
    id: int | None
    order_id: int | None
    product_id: int
    quantity: int
    price: Decimal

    @property
    def line_total(self) -> Decimal:
        return self.price * self.quantity


@dataclass
class Order:
    id: int | None
    customer_id: int
    total_amount: Decimal = Decimal("0")
    order_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    items: list[OrderItem] = field(default_factory=list)

    def add_item(self, product_id: int, quantity: int, price: Decimal) -> OrderItem:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if price < 0:
            raise ValueError("price must be non-negative")
        item = OrderItem(
            id=None,
            order_id=self.id,
            product_id=product_id,
            quantity=quantity,
            price=price,
        )
        self.items.append(item)
        self.recalculate_total()
        return item

    def recalculate_total(self) -> None:
        self.total_amount = sum((item.line_total for item in self.items), Decimal("0"))
