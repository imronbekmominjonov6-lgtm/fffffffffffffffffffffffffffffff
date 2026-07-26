# Guruh/Kanal A'zo Yig'ish Bot (Referal + Obuna tekshirish)

## Ishga tushirish

1. `pip install -r requirements.txt`
2. `config.py` faylida `BOT_TOKEN` ni o'z tokeningizga almashtiring (yoki `BOT_TOKEN` environment variable orqali bering)
3. `python main.py`

## Qanday ishlaydi

- Har bir foydalanuvchi `/start` bosganda o'ziga xos referal havola oladi: `https://t.me/BOT_USERNAME?start=USER_ID`
- Yangi foydalanuvchi shu havola orqali kirib, kerakli kanal(lar)ga obuna bo'lsagina — referal hisoblanadi
- Obuna bo'lmagan foydalanuvchi botdan foydalana olmaydi, "✅ Obuna bo'ldim" tugmasi orqali qayta tekshiradi
- 📊 Reyting — TOP 10 eng ko'p taklif qilganlar
- 👤 Profilim — shaxsiy statistika va keyingi mukofotgacha qancha qolgani
- 🎁 Bonus darajalari — masalan 10 ta taklif = sovg'a (admin sozlaydi)

## Admin panel (`/admin` — faqat admin ID uchun)

- 📊 Statistika — umumiy ko'rsatkichlar
- 📢 Xabar yuborish — barcha foydalanuvchilarga broadcast
- 📺 Kanallar — majburiy kanal qo'shish/o'chirish (**bot kanalda admin bo'lishi shart!**)
- 🎁 Bonus darajalari — mukofot chegaralarini sozlash

## Muhim eslatma

Kanal qo'shishda botni albatta o'sha kanalga **admin** qilib qo'shing, aks holda
bot foydalanuvchining obunasini tekshira olmaydi.

## Render.com'ga deploy qilish

- `PORT` environment variable avtomatik aniqlanadi
- Start command: `python main.py`
- Bot polling va Mini App webserveri **bitta jarayonda** ishlaydi (webapp alohida thread'da)

## 📱 Mini App (Web App)

Botga o'zi ro'yxatdan o'tgan foydalanuvchilar uchun ichki veb-interfeys qo'shildi:

- **Profil** — statistika, keyingi bonusgacha progress
- **Referal havola** — nusxalash va do'stlarga ulashish tugmalari
- **Reyting** — TOP 50 ro'yxati
- **Admin panel** (faqat `config.py` dagi `ADMIN_IDS` ro'yxatidagi ID'lar uchun) — statistika, kanal qo'shish/o'chirish, bonus darajalarini boshqarish

### Ishga tushirish tartibi

1. Botni Render.com'ga deploy qiling (yuqoridagi kabi), Render sizga `https://xxx.onrender.com` manzilini beradi
2. `config.py` dagi (yoki Render environment variables bo'limida) `WEBAPP_URL` ni shu manzilga o'rnating: `WEBAPP_URL=https://xxx.onrender.com`
3. Botni qayta ishga tushiring — endi asosiy menyuda **"📱 Mini App"** tugmasi paydo bo'ladi

### Muhim

- Telegram Mini App **faqat HTTPS** manzillar bilan ishlaydi (Render avtomatik HTTPS beradi)
- `webapp/auth.py` foydalanuvchini Telegram tomonidan yuborilgan `initData`ni HMAC orqali tekshiradi — soxta so'rovlar rad etiladi
- Admin ID'larni ko'paytirish uchun `config.py` dagi `ADMIN_IDS` ro'yxatiga qo'shing
