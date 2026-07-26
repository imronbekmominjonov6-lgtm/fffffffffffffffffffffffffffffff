from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

import database as db
from config import ADMIN_IDS
from keyboards import (
    admin_menu_kb,
    main_menu_kb,
    channels_menu_kb,
    bonus_menu_kb,
    cancel_kb,
)

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_channel_add = State()
    waiting_channel_remove = State()
    waiting_bonus_threshold = State()
    waiting_bonus_reward = State()
    waiting_bonus_remove = State()


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🛠 Admin panelga xush kelibsiz!", reply_markup=admin_menu_kb())


@router.message(F.text == "🔙 Asosiy menyu")
async def back_to_main(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=main_menu_kb(message.from_user.id))


@router.message(F.text == "🔙 Admin menyu")
async def back_to_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("Admin panel:", reply_markup=admin_menu_kb())


@router.message(F.text == "🔙 Bekor qilish")
async def cancel_action(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_menu_kb())


# ---------------- STATISTIKA ----------------

@router.message(F.text == "📊 Statistika")
async def stats_handler(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = db.get_stats()
    channels = db.get_channels()
    tiers = db.get_bonus_tiers()

    text = (
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total']}</b>\n"
        f"🔗 Kamida 1 taklif qilganlar: <b>{stats['with_ref']}</b>\n"
        f"📈 Jami tasdiqlangan takliflar: <b>{stats['total_refs']}</b>\n\n"
        f"📺 Kanallar soni: <b>{len(channels)}</b>\n"
        f"🎁 Bonus darajalari soni: <b>{len(tiers)}</b>"
    )
    await message.answer(text, parse_mode="HTML")


# ---------------- BROADCAST ----------------

@router.message(F.text == "📢 Xabar yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminStates.waiting_broadcast)
    await message.answer(
        "📢 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:",
        reply_markup=cancel_kb(),
    )


@router.message(StateFilter(AdminStates.waiting_broadcast))
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    await state.clear()

    user_ids = db.get_all_user_ids()
    sent, failed = 0, 0
    status_msg = await message.answer(f"⏳ Yuborilmoqda... (0/{len(user_ids)})")

    for i, uid in enumerate(user_ids, start=1):
        try:
            await message.copy_to(chat_id=uid)
            sent += 1
        except Exception:
            failed += 1
            db.block_user(uid)

        if i % 25 == 0:
            try:
                await status_msg.edit_text(f"⏳ Yuborilmoqda... ({i}/{len(user_ids)})")
            except Exception:
                pass

    await message.answer(
        f"✅ Xabar yuborildi!\n📤 Yetkazildi: {sent}\n❌ Yetkazilmadi: {failed}",
        reply_markup=admin_menu_kb(),
    )


# ---------------- KANALLAR ----------------

@router.message(F.text == "📺 Kanallar")
async def channels_menu(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("📺 Kanallar bo'limi:", reply_markup=channels_menu_kb())


@router.message(F.text == "📋 Kanallar ro'yxati")
async def channels_list(message: Message):
    if not is_admin(message.from_user.id):
        return
    channels = db.get_channels()
    if not channels:
        await message.answer("Hozircha majburiy kanal qo'shilmagan.")
        return
    text = "📋 <b>Majburiy kanallar:</b>\n\n" + "\n".join(f"• {c}" for c in channels)
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "➕ Kanal qo'shish")
async def channel_add_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminStates.waiting_channel_add)
    await message.answer(
        "Kanal username'ini kiriting (masalan: @mening_kanalim).\n"
        "⚠️ Bot ushbu kanalda admin bo'lishi shart!",
        reply_markup=cancel_kb(),
    )


@router.message(StateFilter(AdminStates.waiting_channel_add))
async def channel_add_finish(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    channel = message.text.strip()
    if not channel.startswith("@"):
        channel = "@" + channel
    db.add_channel(channel)
    await state.clear()
    await message.answer(f"✅ {channel} kanali qo'shildi!", reply_markup=channels_menu_kb())


@router.message(F.text == "➖ Kanal o'chirish")
async def channel_remove_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    channels = db.get_channels()
    if not channels:
        await message.answer("O'chirish uchun kanal yo'q.")
        return
    await state.set_state(AdminStates.waiting_channel_remove)
    text = "O'chirmoqchi bo'lgan kanal nomini yozing:\n\n" + "\n".join(f"• {c}" for c in channels)
    await message.answer(text, reply_markup=cancel_kb())


@router.message(StateFilter(AdminStates.waiting_channel_remove))
async def channel_remove_finish(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    channel = message.text.strip()
    if not channel.startswith("@"):
        channel = "@" + channel
    db.remove_channel(channel)
    await state.clear()
    await message.answer(f"✅ {channel} o'chirildi!", reply_markup=channels_menu_kb())


# ---------------- BONUS DARAJALARI ----------------

@router.message(F.text == "🎁 Bonus darajalari")
async def bonus_menu(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🎁 Bonus darajalari bo'limi:", reply_markup=bonus_menu_kb())


@router.message(F.text == "📋 Darajalar ro'yxati")
async def bonus_list(message: Message):
    if not is_admin(message.from_user.id):
        return
    tiers = db.get_bonus_tiers()
    if not tiers:
        await message.answer("Hozircha bonus darajasi qo'shilmagan.")
        return
    text = "🎁 <b>Bonus darajalari:</b>\n\n" + "\n".join(
        f"• {t['threshold']} ta → {t['reward']}" for t in tiers
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "➕ Daraja qo'shish")
async def bonus_add_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminStates.waiting_bonus_threshold)
    await message.answer("Nechta taklif uchun bonus beriladi? (raqam kiriting)", reply_markup=cancel_kb())


@router.message(StateFilter(AdminStates.waiting_bonus_threshold))
async def bonus_add_threshold(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, faqat raqam kiriting.")
        return
    await state.update_data(threshold=int(message.text.strip()))
    await state.set_state(AdminStates.waiting_bonus_reward)
    await message.answer("Mukofot matnini kiriting (masalan: 5000 so'm balans):")


@router.message(StateFilter(AdminStates.waiting_bonus_reward))
async def bonus_add_reward(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    threshold = data["threshold"]
    db.add_bonus_tier(threshold, message.text.strip())
    await state.clear()
    await message.answer(
        f"✅ Bonus daraja qo'shildi: {threshold} ta → {message.text.strip()}",
        reply_markup=bonus_menu_kb(),
    )


@router.message(F.text == "➖ Daraja o'chirish")
async def bonus_remove_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    tiers = db.get_bonus_tiers()
    if not tiers:
        await message.answer("O'chirish uchun daraja yo'q.")
        return
    await state.set_state(AdminStates.waiting_bonus_remove)
    text = "O'chirmoqchi bo'lgan daraja raqamini yozing:\n\n" + "\n".join(
        f"• {t['threshold']}" for t in tiers
    )
    await message.answer(text, reply_markup=cancel_kb())


@router.message(StateFilter(AdminStates.waiting_bonus_remove))
async def bonus_remove_finish(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, faqat raqam kiriting.")
        return
    threshold = int(message.text.strip())
    db.remove_bonus_tier(threshold)
    await state.clear()
    await message.answer(f"✅ {threshold} ta daraja o'chirildi!", reply_markup=bonus_menu_kb())
