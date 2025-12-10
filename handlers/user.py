from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from keyboards.reply import main_kb
from keyboards.inline import catalog_kb, product_actions_kb, cart_kb
import database

user_router = Router()

@user_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Вітаю в магазині 'Солодкі Мрії'! 🍬\nТут ви знайдете найкращі букети з цукерок.",
        reply_markup=main_kb
    )

@user_router.message(F.text == "🍬 Каталог")
@user_router.message(Command("catalog"))
async def show_catalog(message: Message):
    products = await database.get_products()
    if not products:
        await message.answer("Каталог наразі порожній.")
        return
    await message.answer("Оберіть букет:", reply_markup=catalog_kb(products))

@user_router.callback_query(F.data == "catalog")
async def back_to_catalog(callback: CallbackQuery):
    await callback.message.delete()
    await show_catalog(callback.message)

@user_router.callback_query(F.data.startswith("view_"))
async def view_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    product = await database.get_product(product_id)
    # product: id, name, desc, price, photo_id
    
    caption = f"<b>{product[1]}</b>\n\n{product[2]}\n\nЦіна: {product[3]} грн"
    await callback.message.answer_photo(
        photo=product[4], 
        caption=caption, 
        reply_markup=product_actions_kb(product[0]),
        parse_mode="HTML"
    )
    await callback.answer()

# --- ЛОГІКА КОШИКА ---

@user_router.callback_query(F.data.startswith("add_to_cart_"))
async def add_item_to_cart(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    await database.add_to_cart(user_id, product_id)
    await callback.answer("✅ Товар додано в кошик!", show_alert=True)

@user_router.message(F.text == "🛒 Кошик")
@user_router.message(Command("cart"))
async def show_cart(message: Message):
    cart_items = await database.get_cart(message.from_user.id)
    
    if not cart_items:
        await message.answer("Ваш кошик порожній 😔\nЗагляньте в каталог!")
        return

    total_price = 0
    cart_text = "<b>🛒 Ваш кошик:</b>\n\n"
    
    for item in cart_items:
        # item: [cart_id, name, price, quantity, product_id]
        item_sum = item[2] * item[3]
        total_price += item_sum
        cart_text += f"🍬 <b>{item[1]}</b>\n{item[3]} шт. x {item[2]} грн = {item_sum} грн\n"
    
    cart_text += f"\n<b>💰 Загальна сума: {total_price} грн</b>"
    
    await message.answer(cart_text, reply_markup=cart_kb(cart_items), parse_mode="HTML")

@user_router.callback_query(F.data.startswith("del_cart_"))
async def delete_item(callback: CallbackQuery):
    cart_id = int(callback.data.split("_")[2])
    await database.delete_item_from_cart(callback.from_user.id, cart_id)
    await callback.message.delete()
    await show_cart(callback.message)

@user_router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery):
    await database.empty_cart(callback.from_user.id)
    await callback.message.edit_text("Кошик очищено 🗑")

# --- ОБРОБНИК INFO ---
@user_router.message(F.text == "ℹ️ Info")
@user_router.message(Command("info"))
async def cmd_info(message: Message):
    # Ви можете використовувати HTML теги для краси
    info_text = (
        "🍬 <b>Магазин 'Солодкі Мрії'</b>\n\n"
        "Ми створюємо унікальні букети з цукерок, які дарують емоції! "
        "Ідеальний подарунок на свято або просто, щоб зробити приємно.\n\n"
        "📍 <b>Наша адреса:</b> м. Київ, вул. Хрещатик, 1\n"
        "⏰ <b>Графік роботи:</b> Пн-Нд з 09:00 до 21:00\n\n"
        "📞 <b>Контакти:</b>\n"
        "+380 99 123 45 67\n"
        "@manager_username"
    )
    
    # Можна додати кнопку-посилання на Instagram або менеджера
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    url_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Наш Instagram", url="https://instagram.com")]
    ])

    await message.answer(info_text, parse_mode="HTML", reply_markup=url_kb)


# --- ОБРОБНИК HELP ---
@user_router.message(F.text == "📞 Help")
@user_router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "🆘 <b>Довідка по користуванню ботом</b>\n\n"
        "<b>Як зробити замовлення?</b>\n"
        "1. Натисніть <b>🍬 Каталог</b>, щоб обрати букет.\n"
        "2. Натисніть кнопку <b>🛒 Додати в кошик</b> під товаром.\n"
        "3. Перейдіть у <b>🛒 Кошик</b> для перевірки замовлення.\n"
        "4. Натисніть <b>✅ Оформити замовлення</b> та оплатіть карткою.\n\n"
        "<b>Команди:</b>\n"
        "/start - Перезапустити бота\n"
        "/catalog - Відкрити каталог\n"
        "/cart - Відкрити кошик\n\n"
        "<i>Якщо у вас виникли проблеми з оплатою або замовленням, напишіть нашому менеджеру.</i>"
    )
    
    await message.answer(help_text, parse_mode="HTML")