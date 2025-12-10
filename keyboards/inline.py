from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def catalog_kb(products):
    builder = InlineKeyboardBuilder()
    for product in products:
        # product: (id, name, desc, price, photo)
        builder.button(text=f"{product[1]} - {product[3]} грн", callback_data=f"view_{product[0]}")
    builder.adjust(1)
    return builder.as_markup()

def product_actions_kb(product_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Додати в кошик", callback_data=f"add_to_cart_{product_id}")],
        [InlineKeyboardButton(text="🔙 Назад до каталогу", callback_data="catalog")]
    ])
    return kb

def cart_kb(cart_items):
    builder = InlineKeyboardBuilder()
    
    # Створюємо кнопку видалення для кожного товару в кошику
    for item in cart_items:
        # item: [cart_id, name, price, quantity, product_id]
        btn_text = f"❌ {item[1]} ({item[3]} шт.)"
        builder.button(text=btn_text, callback_data=f"del_cart_{item[0]}")
    
    builder.adjust(1) # Кнопки одна під одною
    
    # Кнопки управління внизу
    builder.row(
        InlineKeyboardButton(text="🧹 Очистити", callback_data="clear_cart"),
        InlineKeyboardButton(text="✅ Оформити замовлення", callback_data="checkout")
    )
    builder.row(InlineKeyboardButton(text="🔙 До каталогу", callback_data="catalog"))
    
    return builder.as_markup()

# Список товарів для адміна (кнопка веде на налаштування товару)
def admin_catalog_kb(products):
    builder = InlineKeyboardBuilder()
    
    # Кнопка додавання нового товару (вгорі списку)
    builder.row(InlineKeyboardButton(text="➕ Додати новий товар", callback_data="add_new_item"))
    
    # Список існуючих товарів
    for product in products:
        builder.button(text=f"⚙️ {product[1]}", callback_data=f"admin_view_{product[0]}")
    
    builder.adjust(1)
    return builder.as_markup()

# Меню дій з товаром (Редагувати / Видалити / Назад)
def admin_product_actions_kb(product_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редагувати", callback_data=f"edit_start_{product_id}")],
        [InlineKeyboardButton(text="🗑 Видалити", callback_data=f"delete_confirm_{product_id}")],
        [InlineKeyboardButton(text="🔙 Список товарів", callback_data="admin_catalog")]
    ])
    return kb

# Меню вибору, що саме редагувати
def edit_fields_kb(product_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назву", callback_data=f"edit_field_name_{product_id}"),
         InlineKeyboardButton(text="Ціну", callback_data=f"edit_field_price_{product_id}")],
        [InlineKeyboardButton(text="Опис", callback_data=f"edit_field_desc_{product_id}"),
         InlineKeyboardButton(text="Фото", callback_data=f"edit_field_photo_{product_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_view_{product_id}")]
    ])
    return kb

def orders_list_kb(orders):
    builder = InlineKeyboardBuilder()
    if not orders:
        return None
        
    for order in orders:
        # order: (id, user_id, user_name, address, products, total_price, status)
        # Кнопка: "№1 - Іван - 500 грн"
        btn_text = f"№{order[0]} | {order[2]} | {order[5]} грн"
        builder.button(text=btn_text, callback_data=f"admin_order_{order[0]}")
    
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="🔙 Закрити", callback_data="close_admin_orders"))
    return builder.as_markup()

def order_details_kb():
    # Тут можна додати кнопку "Позначити як виконане", якщо розширити логіку
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 До списку замовлень", callback_data="admin_orders_list")]
    ])
    return kb