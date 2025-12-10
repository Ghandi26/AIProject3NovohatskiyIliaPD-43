from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
from utils.states import AdminState, EditProductState
from keyboards.inline import admin_catalog_kb, admin_product_actions_kb, edit_fields_kb, orders_list_kb, order_details_kb
import database

admin_router = Router()

# --- ГОЛОВНЕ МЕНЮ АДМІНА ---
@admin_router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID: return
    
    # Оновлений текст: лише дві основні команди
    await message.answer(
        "👨‍💻 <b>Адмін-панель</b>\n\n"
        "/items - Управління товарами (Список + Додавання)\n"
        "/orders - Перегляд замовлень",
        parse_mode="HTML"
    )

# --- УПРАВЛІННЯ ТОВАРАМИ (/items) ---

@admin_router.message(Command("items"))
async def show_admin_items(message: Message):
    if message.from_user.id != ADMIN_ID: return
    products = await database.get_products()
    
    # Навіть якщо товарів немає, показуємо меню, щоб можна було натиснути "Додати"
    await message.answer("📦 <b>Управління каталогом:</b>", 
                         reply_markup=admin_catalog_kb(products),
                         parse_mode="HTML")
@admin_router.callback_query(F.data == "admin_catalog")
async def back_to_admin_catalog(callback: CallbackQuery):
    # 1. Видаляємо старе повідомлення (бо там було фото, а ми хочемо текст)
    await callback.message.delete()
    
    # 2. Отримуємо товари
    products = await database.get_products()
    
    # 3. Відправляємо нове повідомлення вручну (не викликаючи show_admin_items)
    await callback.message.answer(
        "📦 <b>Управління каталогом:</b>", 
        reply_markup=admin_catalog_kb(products),
        parse_mode="HTML"
    )


# --- ЛОГІКА ДОДАВАННЯ ТОВАРУ (FSM) ---

# Тепер запускається через CallbackQuery (кнопка "Додати новий товар")
@admin_router.callback_query(F.data == "add_new_item")
async def start_add_item(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введіть назву нового товару:")
    await state.set_state(AdminState.waiting_for_name)
    await callback.answer()

@admin_router.message(AdminState.waiting_for_name)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введіть опис товару:")
    await state.set_state(AdminState.waiting_for_desc)

@admin_router.message(AdminState.waiting_for_desc)
async def add_desc(message: Message, state: FSMContext):
    await state.update_data(desc=message.text)
    await message.answer("Введіть ціну (число):")
    await state.set_state(AdminState.waiting_for_price)

@admin_router.message(AdminState.waiting_for_price)
async def add_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await message.answer("Надішліть фото товару:")
        await state.set_state(AdminState.waiting_for_photo)
    except ValueError:
        await message.answer("Будь ласка, введіть коректне число.")

@admin_router.message(AdminState.waiting_for_photo, F.photo)
async def add_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    
    await database.add_product(data['name'], data['desc'], data['price'], photo_id)
    await state.clear()
    
    await message.answer("✅ Товар успішно додано!")
    
    # Одразу показуємо оновлений список товарів
    await show_admin_items(message)


# --- РЕДАГУВАННЯ ТА ВИДАЛЕННЯ (Логіка з попереднього кроку) ---

@admin_router.callback_query(F.data.startswith("admin_view_"))
async def admin_view_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])
    product = await database.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не знайдено", show_alert=True)
        # Оновлюємо список, якщо товар зник
        await show_admin_items(callback.message) 
        return

    caption = f"<b>{product[1]}</b>\nID: {product[0]}\nЦіна: {product[3]} грн\n\n{product[2]}"
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=product[4],
        caption=caption,
        reply_markup=admin_product_actions_kb(product_id),
        parse_mode="HTML"
    )

@admin_router.callback_query(F.data.startswith("delete_confirm_"))
async def delete_product_handler(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])
    await database.delete_product(product_id)
    await callback.answer("✅ Товар видалено!", show_alert=True)
    await callback.message.delete()
    await show_admin_items(callback.message)

@admin_router.callback_query(F.data.startswith("edit_start_"))
async def edit_product_menu(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])
    await callback.message.edit_caption(
        caption="Що ви хочете змінити?",
        reply_markup=edit_fields_kb(product_id),
        parse_mode="HTML"
    )

@admin_router.callback_query(F.data.startswith("edit_field_"))
async def edit_field_start(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    field = parts[2]
    product_id = int(parts[3])
    
    await state.update_data(product_id=product_id, field=field)
    
    text_map = {
        "name": "Введіть нову назву:",
        "price": "Введіть нову ціну (число):",
        "desc": "Введіть новий опис:",
        "photo": "Надішліть нове фото:"
    }
    
    await callback.message.answer(text_map[field])
    await state.set_state(EditProductState.waiting_for_new_value)
    await callback.answer()

@admin_router.message(EditProductState.waiting_for_new_value)
async def save_new_value(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data['product_id']
    field = data['field']
    
    new_value = None
    if field == 'photo':
        if not message.photo:
            await message.answer("Це не фото. Спробуйте ще раз.")
            return
        new_value = message.photo[-1].file_id
    elif field == 'price':
        try:
            new_value = float(message.text)
        except ValueError:
            await message.answer("Ціна має бути числом.")
            return
    else:
        new_value = message.text

    db_field = 'photo_id' if field == 'photo' else field
    await database.update_product_field(product_id, db_field, new_value)
    
    await message.answer("✅ Зміни збережено!")
    await state.clear()
    
    # Повертаємось до перегляду цього товару
    updated_product = await database.get_product(product_id)
    caption = f"<b>{updated_product[1]}</b>\nID: {updated_product[0]}\nЦіна: {updated_product[3]} грн\n\n{updated_product[2]}"
    
    await message.answer_photo(
        photo=updated_product[4],
        caption=caption,
        reply_markup=admin_product_actions_kb(product_id),
        parse_mode="HTML"
    )

# --- ПЕРЕГЛЯД ЗАМОВЛЕНЬ (/orders) ---

@admin_router.message(Command("orders"))
async def show_orders(message: Message):
    if message.from_user.id != ADMIN_ID: return
    
    orders = await database.get_orders()
    if not orders:
        await message.answer("Список замовлень порожній.")
        return
        
    await message.answer("📋 <b>Останні замовлення:</b>", 
                         reply_markup=orders_list_kb(orders), 
                         parse_mode="HTML")

@admin_router.callback_query(F.data == "admin_orders_list")
async def back_to_orders(callback: CallbackQuery):
    # Тут ми можемо використати edit_text, бо і деталі, і список - це текст.
    # Це прибере "миготіння" екрану.
    
    orders = await database.get_orders()
    if not orders:
        await callback.answer("Список замовлень порожній", show_alert=True)
        return
        
    await callback.message.edit_text(
        "📋 <b>Останні замовлення:</b>", 
        reply_markup=orders_list_kb(orders), 
        parse_mode="HTML"
    )

@admin_router.callback_query(F.data == "close_admin_orders")
async def close_orders_list(callback: CallbackQuery):
    await callback.message.delete()

@admin_router.callback_query(F.data.startswith("admin_order_"))
async def view_order_details(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    order = await database.get_order(order_id)
    
    if not order:
        await callback.answer("Замовлення не знайдено.")
        return

    text = (
        f"📦 <b>Замовлення №{order[0]}</b>\n"
        f"👤 Клієнт: {order[2]}\n"
        f"📍 Адреса: {order[3]}\n"
        f"📱 ID Telegram: {order[1]}\n\n"
        f"🛒 <b>Товари:</b>\n{order[4]}\n\n"
        f"💰 <b>Сума: {order[5]} грн</b>\n"
        f"Статус: {order[6]}"
    )
    
    await callback.message.edit_text(text, reply_markup=order_details_kb(), parse_mode="HTML")