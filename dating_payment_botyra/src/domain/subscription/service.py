from src.domain.subscription.entity import Subscription
from src.domain.subscription.events import SubscriptionActivated, SubscriptionExpired


def activate_subscription(subscription: Subscription) -> SubscriptionActivated:
    subscription.activate()
    return SubscriptionActivated(
        subscription_id=subscription.id,
        user_id=subscription.user_id,
        expires_at=subscription.expires_at,
    )


def expire_subscription(subscription: Subscription) -> SubscriptionExpired:
    subscription.expire()
    return SubscriptionExpired(
        subscription_id=subscription.id,
        user_id=subscription.user_id,
    )
