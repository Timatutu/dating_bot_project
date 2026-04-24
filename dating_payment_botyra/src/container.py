from src.application.payment.handlers import (
    CheckCryptoPaymentHandler,
    ConfirmPaymentHandler,
    CreateCryptoPaymentHandler,
    CreatePaymentHandler,
)
from src.application.subscription.handlers import ExpireSubscriptionsHandler, GetSubscriptionHandler
from src.infrastructure.gateways.crypto.eth import EthUsdtGateway
from src.infrastructure.gateways.crypto.sol import SolUsdtGateway
from src.infrastructure.gateways.http_client import HttpClient


class Container:
    def __init__(self) -> None:
        self._uow_factory = None
        self._event_bus = None
        self._http_client: HttpClient | None = None
        self._eth_gateway: EthUsdtGateway | None = None
        self._sol_gateway: SolUsdtGateway | None = None

    def init(
        self,
        uow_factory,
        event_bus,
        http_client: HttpClient,
        eth_gateway: EthUsdtGateway,
        sol_gateway: SolUsdtGateway,
    ) -> None:
        self._uow_factory = uow_factory
        self._event_bus = event_bus
        self._http_client = http_client
        self._eth_gateway = eth_gateway
        self._sol_gateway = sol_gateway

    @property
    def http_client(self) -> HttpClient:
        if self._http_client is None:
            raise RuntimeError("Container is not initialized")
        return self._http_client

    @property
    def eth_gateway(self) -> EthUsdtGateway:
        if self._eth_gateway is None:
            raise RuntimeError("Container is not initialized")
        return self._eth_gateway

    @property
    def sol_gateway(self) -> SolUsdtGateway:
        if self._sol_gateway is None:
            raise RuntimeError("Container is not initialized")
        return self._sol_gateway

    def create_payment_handler(self) -> CreatePaymentHandler:
        return CreatePaymentHandler(self._uow_factory())

    def confirm_payment_handler(self) -> ConfirmPaymentHandler:
        return ConfirmPaymentHandler(self._uow_factory(), self._event_bus)

    def create_crypto_payment_handler(self) -> CreateCryptoPaymentHandler:
        return CreateCryptoPaymentHandler(
            self._uow_factory(),
            self.eth_gateway,
            self.sol_gateway,
        )

    def check_crypto_payment_handler(self) -> CheckCryptoPaymentHandler:
        return CheckCryptoPaymentHandler(
            self._uow_factory(),
            self._event_bus,
            self.eth_gateway,
            self.sol_gateway,
        )

    def get_subscription_handler(self) -> GetSubscriptionHandler:
        return GetSubscriptionHandler(self._uow_factory())

    def expire_subscriptions_handler(self) -> ExpireSubscriptionsHandler:
        return ExpireSubscriptionsHandler(self._uow_factory(), self._event_bus)


container = Container()
