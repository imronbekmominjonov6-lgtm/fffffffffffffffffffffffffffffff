import sqlite3
import json
from config import DB_NAME


def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            referrer_id INTEGER,
            referral_count INTEGER DEFAULT 0,
            referral_confirmed INTEGER DEFAULT 0,
            last_bonus_threshold INTEGER DEFAULT 0,
            joined_at TEXT DEFAULT (datetime('now')),
            is_blocked INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------- USERS ----------------

def user_exists(user_id: int) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row is not None


def add_user(user_id: int, username: str, full_name: str, referrer_id: int = None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO users (user_id, username, full_name, referrer_id) VALUES (?, ?, ?, ?)",
        (user_id, username, full_name, referrer_id),
    )
    conn.commit()
    conn.close()


def get_user(user_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row


def confirm_referral(referrer_id: int) -> int:
    """Referalni tasdiqlaydi va yangi referral_count qiymatini qaytaradi."""
    conn = get_conn()
    conn.execute(
        "UPDATE users SET referral_count = referral_count + 1 WHERE user_id=?",
        (referrer_id,),
    )
    conn.commit()
    row = conn.execute("SELECT referral_count FROM users WHERE user_id=?", (referrer_id,)).fetchone()
    conn.close()
    return row["referral_count"] if row else 0


def mark_referral_confirmed(user_id: int):
    conn = get_conn()
    conn.execute("UPDATE users SET referral_confirmed=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def set_last_bonus_threshold(user_id: int, threshold: int):
    conn = get_conn()
    conn.execute("UPDATE users SET last_bonus_threshold=? WHERE user_id=?", (threshold, user_id))
    conn.commit()
    conn.close()


def get_top_users(limit: int = 10):
    conn = get_conn()
    rows = conn.execute(
        "SELECT user_id, username, full_name, referral_count FROM users "
        "WHERE referral_count > 0 ORDER BY referral_count DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def get_user_rank(user_id: int):
    conn = get_conn()
    user = conn.execute("SELECT referral_count FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return None
    rank_row = conn.execute(
        "SELECT COUNT(*) as cnt FROM users WHERE referral_count > ?", (user["referral_count"],)
    ).fetchone()
    conn.close()
    return rank_row["cnt"] + 1


def get_all_user_ids(only_active: bool = True):
    conn = get_conn()
    if only_active:
        rows = conn.execute("SELECT user_id FROM users WHERE is_blocked=0").fetchall()
    else:
        rows = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    return [r["user_id"] for r in rows]


def block_user(user_id: int):
    conn = get_conn()
    conn.execute("UPDATE users SET is_blocked=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def get_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    with_ref = conn.execute("SELECT COUNT(*) as c FROM users WHERE referral_count > 0").fetchone()["c"]
    total_refs = conn.execute("SELECT SUM(referral_count) as s FROM users").fetchone()["s"] or 0
    conn.close()
    return {"total": total, "with_ref": with_ref, "total_refs": total_refs}


# ---------------- SETTINGS ----------------

def get_setting(key: str, default=None):
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


# ---------------- CHANNELS ----------------

def get_channels():
    raw = get_setting("channels", "[]")
    return json.loads(raw)


def add_channel(channel: str):
    channels = get_channels()
    if channel not in channels:
        channels.append(channel)
        set_setting("channels", json.dumps(channels))


def remove_channel(channel: str):
    channels = get_channels()
    channels = [c for c in channels if c != channel]
    set_setting("channels", json.dumps(channels))


# ---------------- BONUS TIERS ----------------

def get_bonus_tiers():
    raw = get_setting("bonus_tiers", "[]")
    tiers = json.loads(raw)
    return sorted(tiers, key=lambda t: t["threshold"])


def add_bonus_tier(threshold: int, reward: str):
    tiers = get_bonus_tiers()
    tiers.append({"threshold": threshold, "reward": reward})
    set_setting("bonus_tiers", json.dumps(tiers))


def remove_bonus_tier(threshold: int):
    tiers = get_bonus_tiers()
    tiers = [t for t in tiers if t["threshold"] != threshold]
    set_setting("bonus_tiers", json.dumps(tiers))


# ---------------- WEBAPP UCHUN QO'SHIMCHA ----------------

def get_user_dict(user_id: int):
    row = get_user(user_id)
    return dict(row) if row else None


def get_top_users_dicts(limit: int = 50):
    return [dict(r) for r in get_top_users(limit)]
