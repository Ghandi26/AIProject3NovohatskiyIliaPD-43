from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🍬 Каталог"), KeyboardButton(text="🛒 Кошик")],
        [KeyboardButton(text="ℹ️ Info"), KeyboardButton(text="📞 Help")]
    ],
    resize_keyboard=True
)