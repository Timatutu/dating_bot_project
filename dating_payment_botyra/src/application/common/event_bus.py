from abc import ABC, abstractmethod

from src.domain.shared.events import DomainEvent


class IEventBus(ABC):

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None: ...
