from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery, ShippingQuery, ShippingOption
from config import PAYMENT_TOKEN, ADMIN_ID
import database

order_router = Router()

@order_router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    cart_items = await database.get_cart(user_id)
    
    if not cart_items:
        await callback.answer("Кошик порожній!", show_alert=True)
        return

    prices = []
    for item in cart_items:
        # Telegram Payments очікує ціну в копійках (тому множимо на 100)
        # item: [cart_id, name, price, quantity, product_id]
        label = f"{item[1]} (x{item[3]})" 
        amount = int(item[2] * item[3] * 100)
        prices.append(LabeledPrice(label=label, amount=amount))
    
    await bot.send_invoice(
        chat_id=user_id,
        title="Замовлення в 'Солодкі Мрії'",
        description="Оплата замовлення з кошика",
        payload=f"cart_order_{user_id}",
        provider_token=PAYMENT_TOKEN,
        currency="UAH",
        prices=prices,
        start_parameter="create_cart_invoice",
        need_shipping_address=True,
        need_name=True,
        need_phone_number=True,
        is_flexible=True # Увімкнути вибір доставки
    )
    await callback.answer()

# Доставка
@order_router.shipping_query()
async def shipping_check(shipping_query: ShippingQuery):
    options = [
        ShippingOption(
            id='pickup', 
            title='Самовивіз', 
            prices=[
                # ВИПРАВЛЕННЯ: Ціна 0, але вона має бути об'єктом LabeledPrice
                LabeledPrice(label='Безкоштовно', amount=0)
            ]
        ),
        ShippingOption(
            id='express', 
            title='Експрес доставка', 
            prices=[
                LabeledPrice(label='Кур\'єр', amount=10000) # 100.00 грн
            ]
        )
    ]
    await shipping_query.answer(ok=True, shipping_options=options)
# Перевірка перед оплатою
@order_router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

# Успішна оплата
@order_router.message(F.successful_payment)
async def success_payment(message: Message, bot: Bot):
    user_id = message.from_user.id
    pm = message.successful_payment
    
    # 1. Формуємо список товарів
    cart_items = await database.get_cart(user_id)
    products_str = ""
    if cart_items:
        lines = []
        for item in cart_items:
            lines.append(f"{item[1]} (x{item[3]})")
        products_str = ", ".join(lines)
    
    # 2. Формуємо адресу
    order_info = pm.order_info
    user_name = order_info.name if order_info else "Не вказано"
    phone = order_info.phone_number if order_info else "Не вказано"
    email = order_info.email if order_info else "Не вказано"
    
    address_text = "Не вказано"
    if order_info and order_info.shipping_address:
        addr = order_info.shipping_address
        address_text = f"{addr.city}, {addr.street_line1}, {addr.street_line2 or ''}"
    
    total_amount = pm.total_amount / 100
    currency = pm.currency
    
    # 3. Зберігаємо в БД і отримуємо номер замовлення (order_id)
    order_id = await database.add_order(user_id, user_name, address_text, products_str, total_amount)
    
    # 4. Очищуємо кошик клієнта
    await database.empty_cart(user_id)
    
    # 5. --- ПОВІДОМЛЕННЯ КЛІЄНТУ ---
    await message.answer(
        f"✅ Оплата {total_amount} {currency} пройшла успішно!\n"
        f"Номер вашого замовлення: <b>#{order_id}</b>.\n"
        f"Ми вже почали його збирати! 🍬",
        parse_mode="HTML"
    )
    
    # 6. --- ПОВІДОМЛЕННЯ АДМІНУ (ВАМ) ---
    admin_text = (
        f"🚨 <b>НОВЕ ЗАМОВЛЕННЯ №{order_id}</b>\n\n"
        f"👤 <b>Клієнт:</b> {user_name}\n"
        f"📞 <b>Телефон:</b> {phone}\n"
        f"📧 <b>Email:</b> {email}\n"
        f"📍 <b>Адреса:</b> {address_text}\n\n"
        f"🛒 <b>Товари:</b>\n{products_str}\n\n"
        f"💰 <b>Сума: {total_amount} {currency}</b>"
    )
    
    # Відправляємо повідомлення на ваш ADMIN_ID
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")
    except Exception as e:
        print(f"Не вдалося надіслати повідомлення адміну: {e}")