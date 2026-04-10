import json
import logging

import aio_pika

from src.application.common.event_bus import IEventBus
from src.domain.payment.events import PaymentSucceeded
from src.domain.shared.events import DomainEvent
from src.domain.subscription.events import SubscriptionActivated, SubscriptionExpired

logger = logging.getLogger(__name__)

_EVENT_ROUTING_KEYS: dict[type, str] = {
    PaymentSucceeded: "payment.succeeded",
    SubscriptionActivated: "subscription.activated",
    SubscriptionExpired: "subscription.expired",
}


class RabbitMQEventBus(IEventBus):
    def __init__(self, connection: aio_pika.abc.AbstractRobustConnection) -> None:
        self._connection = connection

    async def publish(self, event: DomainEvent) -> None:
        routing_key = _EVENT_ROUTING_KEYS.get(type(event))
        if routing_key is None:
            logger.warning("No routing key for event %s", type(event).__name__)
            return

        channel = await self._connection.channel()
        await channel.declare_queue(routing_key, durable=True)

        payload = {
            "event": type(event).__name__,
            "event_id": str(event.event_id),
            "occurred_at": event.occurred_at.isoformat(),
            **{
                k: str(v) if hasattr(v, "__str__") else v
                for k, v in vars(event).items()
                if k not in ("event_id", "occurred_at")
            },
        }

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )
