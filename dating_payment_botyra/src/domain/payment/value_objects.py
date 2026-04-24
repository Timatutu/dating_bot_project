from dataclasses import dataclass
from enum import Enum

from src.domain.shared.value_object import ValueObject


class Provider(str, Enum):
    TG_STARS = "tg_stars"
    YOOKASSA = "yookassa"
    TON = "ton"
    ETH = "eth"
    SOL = "sol"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass(frozen=True)
class Money(ValueObject):
    amount: int      
    currency: str    
