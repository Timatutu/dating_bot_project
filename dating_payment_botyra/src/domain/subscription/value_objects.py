from dataclasses import dataclass
from enum import Enum

from src.domain.shared.value_object import ValueObject


class Plan(str, Enum):
    MONTH = "month"
    YEAR = "year"


class SubscriptionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"


PLAN_DAYS: dict[Plan, int] = {
    Plan.MONTH: 30,
    Plan.YEAR: 365,
}

PLAN_PRICE_STARS: dict[Plan, int] = {
    Plan.MONTH: 1,
    Plan.YEAR: 1,
}

PLAN_PRICE_USDT: dict[Plan, int] = {
    Plan.MONTH: 5_000_000,   
    Plan.YEAR: 40_000_000,   
}
