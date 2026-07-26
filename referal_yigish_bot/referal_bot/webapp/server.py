import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, render_template

import database as db
from config import ADMIN_IDS
from webapp.auth import validate_init_data

app = Flask(__name__)


def get_authed_user():
    """Header'dagi X-Init-Data orqali foydalanuvchini tasdiqlaydi."""
    init_data = request.headers.get("X-Init-Data", "")
    user = validate_init_data(init_data)
    return user


def error(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/me")
def api_me():
    tg_user = get_authed_user()
    if not tg_user:
        return error("Tasdiqlashda xatolik. Botni Telegram ichida oching.", 401)

    user_id = tg_user["id"]
    if not db.user_exists(user_id):
        db.add_user(user_id, tg_user.get("username", ""), tg_user.get("first_name", ""))

    user = db.get_user_dict(user_id)
    rank = db.get_user_rank(user_id)
    tiers = db.get_bonus_tiers()

    next_tier = None
    for t in tiers:
        if t["threshold"] > user["referral_count"]:
            next_tier = t
            break

    return jsonify({
        "ok": True,
        "user": {
            "id": user_id,
            "name": tg_user.get("first_name", ""),
            "referral_count": user["referral_count"],
            "rank": rank,
            "next_tier": next_tier,
        },
        "is_admin": user_id in ADMIN_IDS,
    })


@app.route("/api/leaderboard")
def api_leaderboard():
    tg_user = get_authed_user()
    if not tg_user:
        return error("Tasdiqlashda xatolik.", 401)

    top = db.get_top_users_dicts(50)
    return jsonify({"ok": True, "leaderboard": top})


@app.route("/api/referral-link")
def api_referral_link():
    tg_user = get_authed_user()
    if not tg_user:
        return error("Tasdiqlashda xatolik.", 401)

    bot_username = os.getenv("BOT_USERNAME", "")
    link = f"https://t.me/{bot_username}?start={tg_user['id']}" if bot_username else ""
    return jsonify({"ok": True, "link": link})


# ---------------- ADMIN API ----------------

def require_admin():
    tg_user = get_authed_user()
    if not tg_user:
        return None, error("Tasdiqlashda xatolik.", 401)
    if tg_user["id"] not in ADMIN_IDS:
        return None, error("Ruxsat yo'q.", 403)
    return tg_user, None


@app.route("/api/admin/stats")
def api_admin_stats():
    tg_user, err = require_admin()
    if err:
        return err
    stats = db.get_stats()
    return jsonify({"ok": True, "stats": stats})


@app.route("/api/admin/channels", methods=["GET"])
def api_admin_channels_list():
    tg_user, err = require_admin()
    if err:
        return err
    return jsonify({"ok": True, "channels": db.get_channels()})


@app.route("/api/admin/channels", methods=["POST"])
def api_admin_channels_add():
    tg_user, err = require_admin()
    if err:
        return err
    data = request.get_json(force=True, silent=True) or {}
    channel = (data.get("channel") or "").strip()
    if not channel:
        return error("Kanal nomi bo'sh bo'lmasin.")
    if not channel.startswith("@"):
        channel = "@" + channel
    db.add_channel(channel)
    return jsonify({"ok": True, "channels": db.get_channels()})


@app.route("/api/admin/channels", methods=["DELETE"])
def api_admin_channels_remove():
    tg_user, err = require_admin()
    if err:
        return err
    data = request.get_json(force=True, silent=True) or {}
    channel = (data.get("channel") or "").strip()
    db.remove_channel(channel)
    return jsonify({"ok": True, "channels": db.get_channels()})


@app.route("/api/admin/bonus-tiers", methods=["GET"])
def api_admin_bonus_list():
    tg_user, err = require_admin()
    if err:
        return err
    return jsonify({"ok": True, "tiers": db.get_bonus_tiers()})


@app.route("/api/admin/bonus-tiers", methods=["POST"])
def api_admin_bonus_add():
    tg_user, err = require_admin()
    if err:
        return err
    data = request.get_json(force=True, silent=True) or {}
    threshold = data.get("threshold")
    reward = (data.get("reward") or "").strip()
    if not isinstance(threshold, int) or threshold <= 0 or not reward:
        return error("Noto'g'ri ma'lumot: threshold (musbat son) va reward kerak.")
    db.add_bonus_tier(threshold, reward)
    return jsonify({"ok": True, "tiers": db.get_bonus_tiers()})


@app.route("/api/admin/bonus-tiers", methods=["DELETE"])
def api_admin_bonus_remove():
    tg_user, err = require_admin()
    if err:
        return err
    data = request.get_json(force=True, silent=True) or {}
    threshold = data.get("threshold")
    if not isinstance(threshold, int):
        return error("Noto'g'ri threshold.")
    db.remove_bonus_tier(threshold)
    return jsonify({"ok": True, "tiers": db.get_bonus_tiers()})


if __name__ == "__main__":
    db.init_db()
    port = int(os.getenv("WEBAPP_PORT", 5000))
    app.run(host="0.0.0.0", port=port)
