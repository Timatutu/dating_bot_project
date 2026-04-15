from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.customer.entity import Customer
from app.domain.customer.repository import ICustomerRepository
from app.infrastructure.db.models import CustomerModel


def _to_domain(row: CustomerModel) -> Customer:
    return Customer(
        id=row.id,
        first_name=row.first_name,
        last_name=row.last_name,
        email=row.email,
    )


class CustomerRepository(ICustomerRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, customer_id: int) -> Customer | None:
        row = await self._session.get(CustomerModel, customer_id)
        return _to_domain(row) if row else None

    async def get_by_email(self, email: str) -> Customer | None:
        result = await self._session.execute(
            select(CustomerModel).where(CustomerModel.email == email)
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def add(self, customer: Customer) -> Customer:
        row = CustomerModel(
            first_name=customer.first_name,
            last_name=customer.last_name,
            email=customer.email,
        )
        self._session.add(row)
        await self._session.flush()
        return _to_domain(row)

    async def update_email(self, customer_id: int, new_email: str) -> Customer:
        result = await self._session.execute(
            update(CustomerModel)
            .where(CustomerModel.id == customer_id)
            .values(email=new_email)
            .returning(CustomerModel)
        )
        row = result.scalar_one()
        return _to_domain(row)
