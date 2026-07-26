import os

# Bot tokeni - agar environment variable bo'lmasa shu default ishlatiladi
BOT_TOKEN = os.getenv("BOT_TOKEN", "8923651324:AAGfucuLt1CnZfHiu3YGe1EqvnuaaPRxq3s")

# Adminlar ro'yxati (bir nechta admin bo'lishi mumkin)
ADMIN_IDS = [8642218989, 8155876425]

# Orqaga moslik uchun (ba'zi joylarda ADMIN_ID ishlatilgan bo'lishi mumkin)
ADMIN_ID = ADMIN_IDS[0]

# Ma'lumotlar bazasi fayli
DB_NAME = "referal_bot.db"

# Referal linkida ishlatiladigan bot username (kod ichida avtomatik ham aniqlanadi)
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

# Mini App (Web App) joylashgan HTTPS manzil - deploy qilingandan keyin shu yerga yozing
# Masalan: https://sizning-bot.onrender.com
WEBAPP_URL = os.getenv("WEBAPP_URL", "")
