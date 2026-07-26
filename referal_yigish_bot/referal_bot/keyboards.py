from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import WEBAPP_URL, ADMIN_IDS


def main_menu_kb(user_id: int = None) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="🔗 Referal havolam"), KeyboardButton(text="📊 Reyting"))
    kb.row(KeyboardButton(text="👤 Profilim"), KeyboardButton(text="ℹ️ Yordam"))
    if WEBAPP_URL and user_id in ADMIN_IDS:
        kb.row(KeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=WEBAPP_URL)))
    return kb.as_markup(resize_keyboard=True)


def check_subscribe_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="✅ Obuna bo'ldim"))
    return kb.as_markup(resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="🔙 Bekor qilish"))
    return kb.as_markup(resize_keyboard=True)


def admin_menu_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📢 Xabar yuborish"))
    kb.row(KeyboardButton(text="📺 Kanallar"), KeyboardButton(text="🎁 Bonus darajalari"))
    if WEBAPP_URL:
        kb.row(KeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=WEBAPP_URL)))
    kb.row(KeyboardButton(text="🔙 Asosiy menyu"))
    return kb.as_markup(resize_keyboard=True)


def channels_menu_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="➕ Kanal qo'shish"), KeyboardButton(text="➖ Kanal o'chirish"))
    kb.row(KeyboardButton(text="📋 Kanallar ro'yxati"))
    kb.row(KeyboardButton(text="🔙 Admin menyu"))
    return kb.as_markup(resize_keyboard=True)


def bonus_menu_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="➕ Daraja qo'shish"), KeyboardButton(text="➖ Daraja o'chirish"))
    kb.row(KeyboardButton(text="📋 Darajalar ro'yxati"))
    kb.row(KeyboardButton(text="🔙 Admin menyu"))
    return kb.as_markup(resize_keyboard=True)
