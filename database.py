import aiosqlite
from config import DB_NAME

async def create_tables():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                desc TEXT,
                price REAL,
                photo_id TEXT
            )
        ''')
        # ОНОВЛЕНА ТАБЛИЦЯ ЗАМОВЛЕНЬ (Додано колонку products)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                address TEXT,
                products TEXT, 
                total_price REAL,
                status TEXT DEFAULT 'new'
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        ''')
        await db.commit()
# --- Товари ---
async def add_product(name, desc, price, photo_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT INTO products (name, desc, price, photo_id) VALUES (?, ?, ?, ?)',
                         (name, desc, price, photo_id))
        await db.commit()

async def get_products():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT * FROM products') as cursor:
            return await cursor.fetchall()

async def get_product(product_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT * FROM products WHERE id = ?', (product_id,)) as cursor:
            return await cursor.fetchone()

# --- Кошик ---
async def add_to_cart(user_id, product_id):
    async with aiosqlite.connect(DB_NAME) as db:
        # Перевіряємо, чи є вже цей товар у кошику цього користувача
        cursor = await db.execute('SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?', (user_id, product_id))
        item = await cursor.fetchone()
        
        if item:
            # Якщо є, збільшуємо кількість
            await db.execute('UPDATE cart SET quantity = quantity + 1 WHERE user_id = ? AND product_id = ?', (user_id, product_id))
        else:
            # Якщо немає, додаємо новий запис
            await db.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)', (user_id, product_id))
        await db.commit()

async def get_cart(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        # Отримуємо дані з кошика разом із даними про товар (Join)
        query = '''
            SELECT cart.id, products.name, products.price, cart.quantity, products.id 
            FROM cart 
            JOIN products ON cart.product_id = products.id 
            WHERE cart.user_id = ?
        '''
        async with db.execute(query, (user_id,)) as cursor:
            return await cursor.fetchall()

async def delete_item_from_cart(user_id, cart_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM cart WHERE user_id = ? AND id = ?', (user_id, cart_id))
        await db.commit()

async def empty_cart(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await db.commit()

# Видалення товару (і очищення його з кошиків)
async def delete_product(product_id):
    async with aiosqlite.connect(DB_NAME) as db:
        # Спочатку видаляємо цей товар з усіх кошиків
        await db.execute('DELETE FROM cart WHERE product_id = ?', (product_id,))
        # Тепер видаляємо сам товар
        await db.execute('DELETE FROM products WHERE id = ?', (product_id,))
        await db.commit()

# Оновлення конкретного поля товару
async def update_product_field(product_id, field, value):
    # field може бути: 'name', 'desc', 'price', 'photo_id'
    allowed_fields = ['name', 'desc', 'price', 'photo_id']
    if field not in allowed_fields:
        return
    
    async with aiosqlite.connect(DB_NAME) as db:
        query = f'UPDATE products SET {field} = ? WHERE id = ?'
        await db.execute(query, (value, product_id))
        await db.commit()

# --- ЗАМОВЛЕННЯ ---

async def add_order(user_id, user_name, address, products_str, total_price):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''
            INSERT INTO orders (user_id, user_name, address, products, total_price, status)
            VALUES (?, ?, ?, ?, ?, 'new')
        ''', (user_id, user_name, address, products_str, total_price))
        await db.commit()
        
        # ПОВЕРТАЄМО ID НОВОГО ЗАМОВЛЕННЯ
        return cursor.lastrowid

async def get_orders():
    async with aiosqlite.connect(DB_NAME) as db:
        # Беремо останні 10 замовлень
        async with db.execute('SELECT * FROM orders ORDER BY id DESC LIMIT 10') as cursor:
            return await cursor.fetchall()

async def get_order(order_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)) as cursor:
            return await cursor.fetchone()