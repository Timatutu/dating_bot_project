from dataclasses import dataclass

from app.domain.customer.entity import Customer
from app.domain.shared.uow import IUnitOfWork


class CustomerNotFoundError(Exception):
    pass


class EmailAlreadyUsedError(Exception):
    pass


@dataclass
class UpdateCustomerEmailCommand:
    customer_id: int
    new_email: str


class UpdateCustomerEmailUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, command: UpdateCustomerEmailCommand) -> Customer:
        async with self._uow as uow:
            customer = await uow.customers.get_by_id(command.customer_id)
            if customer is None:
                raise CustomerNotFoundError(f"customer {command.customer_id} not found")

            new_email = command.new_email.strip().lower()
            existing = await uow.customers.get_by_email(new_email)
            if existing is not None and existing.id != customer.id:
                raise EmailAlreadyUsedError(f"email {new_email} already used")

            customer.change_email(new_email)
            updated = await uow.customers.update_email(customer.id, customer.email)
            await uow.commit()
            return updated
