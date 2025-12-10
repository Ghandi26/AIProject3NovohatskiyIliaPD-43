import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
PAYMENT_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")
DB_NAME = 'candy_shop.db'