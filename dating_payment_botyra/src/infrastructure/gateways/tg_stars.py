from src.application.payment.ports import IPaymentGateway
from src.domain.payment.entity import Payment


class TgStarsGateway(IPaymentGateway):

    async def create(self, payment: Payment) -> dict:
        return {
            "title": "Подписка lovebinto",
            "description": "Доступ ко всем функциям",
            "payload": str(payment.id),  
            "currency": "XTR",
            "prices": [{"label": "Подписка", "amount": payment.amount.amount}],
            "provider_token": "",        
        }
