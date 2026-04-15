from app.application.customer.update_email import UpdateCustomerEmailUseCase
from app.application.order.place_order import PlaceOrderUseCase
from app.application.product.add_product import AddProductUseCase
from app.domain.shared.uow import IUnitOfWork
from app.infrastructure.db.session import AsyncSessionLocal
from app.infrastructure.db.uow import SqlAlchemyUnitOfWork


def get_uow() -> IUnitOfWork:
    return SqlAlchemyUnitOfWork(AsyncSessionLocal)


def get_place_order_use_case() -> PlaceOrderUseCase:
    return PlaceOrderUseCase(get_uow())


def get_update_email_use_case() -> UpdateCustomerEmailUseCase:
    return UpdateCustomerEmailUseCase(get_uow())


def get_add_product_use_case() -> AddProductUseCase:
    return AddProductUseCase(get_uow())
