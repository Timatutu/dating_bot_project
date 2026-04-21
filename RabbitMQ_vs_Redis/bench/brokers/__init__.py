from bench.brokers.rabbit import RabbitBroker
from bench.brokers.redis_stream import RedisBroker
from bench.core import Broker, Settings


def make_broker(name: str, settings: Settings) -> Broker:
    key = name.lower()
    if key == "rabbitmq":
        return RabbitBroker(settings)
    if key == "redis":
        return RedisBroker(settings)
    raise ValueError(f"unknown broker: {name}")


__all__ = ["RabbitBroker", "RedisBroker", "make_broker"]
