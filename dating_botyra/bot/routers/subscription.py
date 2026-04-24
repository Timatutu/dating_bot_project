import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from bot.keyboards.profile import (
    check_crypto_payment_kb,
    crypto_plans_kb,
    main_menu,
    subscription_plans_kb,
)
from bot.services.payment_client import PaymentClient
from bot.services.subscription_sync import sync_subscription_from_payment
from common.db.models.user import User

router = Router()
logger = logging.getLogger(__name__)



@router.message(F.text == "💎 Подписка")
async def subscription_info(
    message: Message,
    user: User,
    payment_client: PaymentClient,
    state: FSMContext,
) -> None:
    await state.clear()
    sub = await payment_client.get_subscription(user.id)
    if sub and sub["is_active"]:
        plan_label = "1 месяц" if sub["plan"] == "month" else "1 год"
        expires = sub["expires_at"][:10] if sub["expires_at"] else "—"
        await message.answer(
            f"✅ <b>У вас уже есть активная подписка!</b>\n\n"
            f"План: <b>{plan_label}</b>\n"
            f"Действует до: <b>{expires}</b>",
        )
        return

    await message.answer(
        "💎 <b>Подписка lovebinto</b>\n\n"
        "Открывает доступ ко всем функциям: свайп-лента, совпадения, чат.\n\n"
        "Выбери план:",
        reply_markup=subscription_plans_kb(),
    )


@router.callback_query(F.data.in_({"sub:month", "sub:year"}))
async def choose_plan(
    callback: CallbackQuery,
    user: User,
    payment_client: PaymentClient,
) -> None:
    plan = callback.data.split(":")[1]  

    result = await payment_client.create_payment(user.id, plan)
    if result is None:
        await callback.message.answer("⚠️ Сервис оплаты недоступен. Попробуй позже.")
        await callback.answer()
        return

    payment_id, stars_amount = result
    plan_label = "1 месяц" if plan == "month" else "1 год"

    await callback.message.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Подписка lovebinto — {plan_label}",
        description="Доступ ко всем функциям на весь период",
        payload=str(payment_id),        
        currency="XTR",                
        prices=[LabeledPrice(label=plan_label, amount=stars_amount)],
        provider_token="",              
    )
    await callback.answer()



@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment(
    message: Message,
    user: User,
    payment_client: PaymentClient,
) -> None:
    payment_id = message.successful_payment.invoice_payload
    charge_id = message.successful_payment.telegram_payment_charge_id

    confirmed = await payment_client.confirm_payment(payment_id, charge_id)

    if confirmed:
        await sync_subscription_from_payment(payment_client, user.id)
        await message.answer(
            "✅ <b>Подписка активирована!</b>\n\n"
            "Теперь тебе доступны все функции lovebinto. Наслаждайся! 🎉",
            reply_markup=main_menu(),
        )
    else:
        logger.error("Failed to confirm payment %s charge %s", payment_id, charge_id)
        await message.answer(
            "✅ Оплата прошла, но активация задержалась.\n"
            "Подписка будет активирована в течение минуты."
        )



@router.callback_query(F.data == "sub:crypto")
async def crypto_menu(callback: CallbackQuery, user: User) -> None:
    await callback.message.edit_text(
        "💰 <b>Оплата криптой USDT</b>\n\n"
        "Выбери план:",
        reply_markup=crypto_plans_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "crypto:back")
async def crypto_back(callback: CallbackQuery, user: User) -> None:
    await callback.message.edit_text(
        "💎 <b>Подписка lovebinto</b>\n\n"
        "Открывает доступ ко всем функциям: свайп-лента, совпадения, чат.\n\n"
        "Выбери план:",
        reply_markup=subscription_plans_kb(),
    )
    await callback.answer()


@router.callback_query(
    F.data.in_(
        {
            "crypto:eth:month",
            "crypto:eth:year",
            "crypto:sol:month",
            "crypto:sol:year",
        }
    )
)
async def create_crypto_payment(
    callback: CallbackQuery,
    user: User,
    payment_client: PaymentClient,
) -> None:
    _, provider, plan = callback.data.split(":")

    result = await payment_client.create_crypto_payment(user.id, plan, provider=provider)
    if result is None:
        await callback.message.answer("⚠️ Крипто-оплата временно недоступна. Попробуй позже.")
        await callback.answer()
        return

    payment_id = result["payment_id"]
    address = result["deposit_address"]
    usdt_display = result["usdt_display"]
    expires_at = result["expires_at"]

    if provider == "eth":
        network_text = "Ethereum Sepolia (тест), USDT ERC-20"
        title = "Оплата USDT (ERC-20)"
    else:
        network_text = "Solana Devnet (тест), USDT SPL"
        title = "Оплата USDT (Solana SPL)"

    await callback.message.edit_text(
        f"💰 <b>{title}</b>\n\n"
        f"Отправь <b>{usdt_display} USDT</b> на адрес:\n\n"
        f"<code>{address}</code>\n\n"
        f"⏱ Время на оплату: <b>15 минут</b>\n"
        f"⚠️ Сеть: <b>{network_text}</b>\n\n"
        "После отправки нажми кнопку ниже для проверки.",
        reply_markup=check_crypto_payment_kb(payment_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("check_crypto:"))
async def check_crypto(
    callback: CallbackQuery,
    user: User,
    payment_client: PaymentClient,
) -> None:
    payment_id = callback.data.split(":", 1)[1]

    result = await payment_client.check_crypto_payment(payment_id)
    if result is None:
        await callback.answer("⚠️ Ошибка проверки. Попробуй ещё раз.", show_alert=True)
        return

    status = result["status"]

    if status == "succeeded":
        await sync_subscription_from_payment(payment_client, user.id)
        tx_hash = result.get("tx_hash", "")
        await callback.message.edit_text(
            "✅ <b>Оплата получена! Подписка активирована!</b>\n\n"
            f"TX: <code>{tx_hash[:16]}...</code>\n\n"
            "Наслаждайся всеми функциями lovebinto! 🎉",
        )
        await callback.answer()

    elif status == "expired":
        await callback.message.edit_text(
            "⏰ <b>Время на оплату истекло.</b>\n\n"
            "Платёж отменён. Ты можешь создать новый.",
            reply_markup=subscription_plans_kb(),
        )
        await callback.answer()

    elif status == "failed":
        await callback.message.edit_text(
            "❌ <b>Платёж не найден или отменён.</b>\n\n"
            "Попробуй создать новый.",
            reply_markup=subscription_plans_kb(),
        )
        await callback.answer()

    else:
        await callback.answer(
            "⏳ Оплата ещё не поступила. Подожди и проверь снова.",
            show_alert=True,
        )
