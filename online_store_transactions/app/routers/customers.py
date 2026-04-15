from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Customer
from app.schemas import CustomerCreate, CustomerOut, EmailUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreate,
    session: AsyncSession = Depends(get_session),
) -> CustomerOut:
    async with session.begin():
        existing = await session.scalar(select(Customer).where(Customer.email == str(payload.email)))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already used")
        customer = Customer(first_name=payload.first_name, last_name=payload.last_name, email=str(payload.email))
        session.add(customer)
        await session.flush()
        return CustomerOut(
            customer_id=customer.customer_id,
            first_name=customer.first_name,
            last_name=customer.last_name,
            email=customer.email,
        )


@router.patch("/{customer_id}/email", response_model=CustomerOut, summary="Scenario 2: atomic email update")
async def update_email(
    customer_id: int,
    payload: EmailUpdate,
    session: AsyncSession = Depends(get_session),
) -> CustomerOut:
    async with session.begin():
        customer = await session.get(Customer, customer_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"customer {customer_id} not found")

        new_email = str(payload.email)
        taken = await session.scalar(select(Customer).where(Customer.email == new_email))
        if taken and taken.customer_id != customer_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already used")

        await session.execute(
            update(Customer).where(Customer.customer_id == customer_id).values(email=new_email)
        )
        await session.refresh(customer)
        return CustomerOut(
            customer_id=customer.customer_id,
            first_name=customer.first_name,
            last_name=customer.last_name,
            email=new_email,
        )
