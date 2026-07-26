from aiogram import Router, Bot, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

import database as db
from keyboards import main_menu_kb, check_subscribe_kb

router = Router()


async def is_subscribed_to_all(bot: Bot, user_id: int) -> list:
    """Obuna bo'lmagan kanallar ro'yxatini qaytaradi. Bo'sh list = hammasiga obuna."""
    channels = db.get_channels()
    not_subscribed = []
    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ("left", "kicked"):
                not_subscribed.append(channel)
        except TelegramBadRequest:
            # Bot kanalda admin emas yoki kanal topilmadi - o'tkazib yuboramiz
            continue
    return not_subscribed


async def send_subscribe_prompt(message: Message, not_subscribed: list):
    text = "📢 Botdan foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling:\n\n"
    for ch in not_subscribed:
        link = ch if ch.startswith("@") else ch
        text += f"👉 https://t.me/{link.lstrip('@')}\n"
    text += "\nObuna bo'lgach, pastdagi tugmani bosing 👇"
    await message.answer(text, reply_markup=check_subscribe_kb())


async def finalize_join(message: Message, bot: Bot, user_id: int):
    """Obuna tasdiqlangach chaqiriladi: referalni hisoblaydi va asosiy menyuni ko'rsatadi."""
    user = db.get_user(user_id)
    if user and user["referrer_id"] and not user["referral_confirmed"]:
        db.mark_referral_confirmed(user_id)
        referrer_id = user["referrer_id"]
        new_count = db.confirm_referral(referrer_id)

        try:
            await bot.send_message(
                referrer_id,
                f"🎉 Sizning havolangiz orqali yangi a'zo qo'shildi!\n"
                f"Jami taklif qilganlaringiz: <b>{new_count}</b> ta",
                parse_mode="HTML",
            )
        except Exception:
            pass

        await check_and_notify_bonus(bot, referrer_id, new_count)

    await message.answer(
        "✅ Xush kelibsiz! Asosiy menyu:",
        reply_markup=main_menu_kb(user_id),
    )


async def check_and_notify_bonus(bot: Bot, user_id: int, count: int):
    tiers = db.get_bonus_tiers()
    user = db.get_user(user_id)
    last_threshold = user["last_bonus_threshold"] if user else 0

    for tier in tiers:
        threshold = tier["threshold"]
        if count >= threshold and threshold > last_threshold:
            db.set_last_bonus_threshold(user_id, threshold)
            try:
                await bot.send_message(
                    user_id,
                    f"🎁 Tabriklaymiz! Siz <b>{threshold}</b> ta do'st taklif qildingiz!\n"
                    f"Mukofotingiz: {tier['reward']}",
                    parse_mode="HTML",
                )
            except Exception:
                pass


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, command: CommandObject):
    user_id = message.from_user.id
    is_new = not db.user_exists(user_id)

    if is_new:
        referrer_id = None
        if command.args and command.args.isdigit():
            ref_id = int(command.args)
            if ref_id != user_id and db.user_exists(ref_id):
                referrer_id = ref_id

        db.add_user(
            user_id=user_id,
            username=message.from_user.username or "",
            full_name=message.from_user.full_name or "",
            referrer_id=referrer_id,
        )

    not_subscribed = await is_subscribed_to_all(bot, user_id)
    if not_subscribed:
        await send_subscribe_prompt(message, not_subscribed)
        return

    await finalize_join(message, bot, user_id)


@router.message(F.text == "✅ Obuna bo'ldim")
async def check_subscription_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    if not db.user_exists(user_id):
        db.add_user(user_id, message.from_user.username or "", message.from_user.full_name or "")

    not_subscribed = await is_subscribed_to_all(bot, user_id)
    if not_subscribed:
        await message.answer("❗️ Siz hali barcha kanallarga obuna bo'lmadingiz. Qaytadan tekshiring.")
        await send_subscribe_prompt(message, not_subscribed)
        return

    await finalize_join(message, bot, user_id)


@router.message(F.text == "🔗 Referal havolam")
async def referral_link_handler(message: Message, bot: Bot):
    me = await bot.get_me()
    user_id = message.from_user.id
    link = f"https://t.me/{me.username}?start={user_id}"
    user = db.get_user(user_id)
    count = user["referral_count"] if user else 0
    await message.answer(
        f"🔗 Sizning shaxsiy referal havolangiz:\n{link}\n\n"
        f"Ushbu havola orqali <b>{count}</b> ta do'stingizni taklif qilgansiz.\n"
        f"Do'stlaringiz kanalga obuna bo'lgach, avtomatik hisoblanadi.",
        parse_mode="HTML",
    )


@router.message(F.text == "📊 Reyting")
async def rating_handler(message: Message):
    top = db.get_top_users(10)
    if not top:
        await message.answer("Hozircha reytingda hech kim yo'q.")
        return

    medals = ["🥇", "🥈", "🥉"]
    text = "📊 <b>Eng faol takliflar reytingi (TOP 10)</b>\n\n"
    for i, row in enumerate(top):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = row["full_name"] or (f"@{row['username']}" if row["username"] else "Foydalanuvchi")
        text += f"{medal} {name} — <b>{row['referral_count']}</b> ta\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "👤 Profilim")
async def profile_handler(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    if not user:
        await message.answer("Ma'lumot topilmadi, /start bosing.")
        return

    rank = db.get_user_rank(user_id)
    tiers = db.get_bonus_tiers()
    next_tier = None
    for tier in tiers:
        if tier["threshold"] > user["referral_count"]:
            next_tier = tier
            break

    text = (
        f"👤 <b>Profilingiz</b>\n\n"
        f"Taklif qilganlar: <b>{user['referral_count']}</b> ta\n"
        f"Reytingdagi o'rningiz: <b>{rank}</b>\n"
    )
    if next_tier:
        qoldi = next_tier["threshold"] - user["referral_count"]
        text += f"\n🎯 Keyingi mukofotgacha: <b>{qoldi}</b> ta taklif qoldi\n"
        text += f"Mukofot: {next_tier['reward']}"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "ℹ️ Yordam")
async def help_handler(message: Message):
    await message.answer(
        "ℹ️ <b>Bot haqida</b>\n\n"
        "🔗 Referal havolam — shaxsiy taklif havolangizni oling\n"
        "📊 Reyting — eng faol foydalanuvchilar\n"
        "👤 Profilim — statistikangiz va keyingi mukofot\n\n"
        "Do'stingiz sizning havolangiz orqali kirib, kerakli kanal(lar)ga "
        "obuna bo'lsa, taklifingiz avtomatik hisoblanadi.",
        parse_mode="HTML",
    )
