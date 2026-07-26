import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from config import BOT_TOKEN


def validate_init_data(init_data: str, max_age_seconds: int = 86400):
    """
    Telegram WebApp initData'ni tekshiradi va foydalanuvchi ma'lumotini qaytaradi.
    Muvaffaqiyatsiz bo'lsa None qaytaradi.
    Rasmiy Telegram hujjatiga asoslangan: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not init_data:
        return None

    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        return None

    auth_date = int(parsed.get("auth_date", 0))
    import time
    if max_age_seconds and (time.time() - auth_date) > max_age_seconds:
        return None

    user_raw = parsed.get("user")
    if not user_raw:
        return None

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError:
        return None

    return user
