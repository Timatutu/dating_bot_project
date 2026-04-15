from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class CustomerCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class CustomerOut(BaseModel):
    customer_id: int
    first_name: str
    last_name: str
    email: str


class EmailUpdate(BaseModel):
    email: EmailStr


class ProductCreate(BaseModel):
    product_name: str
    price: Decimal = Field(ge=0)


class ProductOut(BaseModel):
    product_id: int
    product_name: str
    price: Decimal


class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    customer_id: int
    items: list[OrderItemIn] = Field(min_length=1)


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    subtotal: Decimal


class OrderOut(BaseModel):
    order_id: int
    customer_id: int
    order_date: datetime
    total_amount: Decimal
    items: list[OrderItemOut]
