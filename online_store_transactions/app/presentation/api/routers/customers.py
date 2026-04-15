from fastapi import APIRouter, Depends, HTTPException, status

from app.application.customer.update_email import (
    CustomerNotFoundError,
    EmailAlreadyUsedError,
    UpdateCustomerEmailCommand,
    UpdateCustomerEmailUseCase,
)
from app.domain.customer.entity import Customer
from app.presentation.api.deps import get_update_email_use_case, get_uow
from app.presentation.api.schemas import CustomerCreate, CustomerOut, EmailUpdate
from app.domain.shared.uow import IUnitOfWork

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreate,
    uow: IUnitOfWork = Depends(get_uow),
) -> CustomerOut:
    async with uow as u:
        existing = await u.customers.get_by_email(str(payload.email))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already used")
        customer = await u.customers.add(
            Customer(id=None, first_name=payload.first_name, last_name=payload.last_name, email=str(payload.email))
        )
        await u.commit()
    return CustomerOut(id=customer.id, first_name=customer.first_name, last_name=customer.last_name, email=customer.email)


@router.patch("/{customer_id}/email", response_model=CustomerOut)
async def update_email(
    customer_id: int,
    payload: EmailUpdate,
    use_case: UpdateCustomerEmailUseCase = Depends(get_update_email_use_case),
) -> CustomerOut:
    try:
        customer = await use_case.execute(
            UpdateCustomerEmailCommand(customer_id=customer_id, new_email=payload.email)
        )
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmailAlreadyUsedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return CustomerOut(id=customer.id, first_name=customer.first_name, last_name=customer.last_name, email=customer.email)
