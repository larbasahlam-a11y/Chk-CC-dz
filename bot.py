#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Profesor Checker v11.0 ULTIMATE - Fixed

import telebot, requests, random, re, json, uuid, string, time, threading, os
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, InputMediaPhoto
from faker import Faker
from config import *
from gateways import *

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
faker = Faker()

command_usage = {}
user_codes = {}
user_proxies = {}
banned_users = []
admin_sessions = {}
user_stats = {}
pending_activation = {}
successful_cards = {}
mass_sessions = {}

# ═══════════════════════════════════════════════════════════════
# دوال مساعدة
# ═══════════════════════════════════════════════════════════════

def generate_code():
    chars = string.ascii_uppercase + string.digits
    return '-'.join([''.join(random.choices(chars, k=4)) for _ in range(3)])

def get_user_code(user_id):
    for code, data in user_codes.items():
        if data.get('user_id') == str(user_id): return code
    return None

def is_code_valid(code):
    if not code or code not in user_codes: return False
    expiry = user_codes[code].get('expiry')
    if expiry and datetime.now() < expiry: return True
    if not expiry: return True
    return False

def is_user_premium(user_id):
    if str(user_id) == str(ADMIN_ID): return True
    if is_code_valid(get_user_code(user_id)): return True
    for code, data in user_codes.items():
        if data.get('user_id') == str(user_id) and data.get('type') == 'stars':
            if datetime.now() < data.get('expiry', datetime.now()): return True
    return False

def parse_proxy(proxy_str):
    if ':' in proxy_str:
        parts = proxy_str.split(':')
        if len(parts) == 2: return {'http': f'http://{parts[0]}:{parts[1]}', 'https': f'http://{parts[0]}:{parts[1]}'}
        elif len(parts) == 4: return {'http': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}', 'https': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}'}
    return None

def add_user_proxy(user_id, proxy_str):
    if user_id not in user_proxies: user_proxies[user_id] = []
    proxy = parse_proxy(proxy_str)
    if proxy: user_proxies[user_id].append(proxy); return True
    return False

def update_stats(user_id, status):
    if user_id not in user_stats: user_stats[user_id] = {'total': 0, 'charged': 0, 'funds': 0, 'ccn': 0, 'declined': 0}
    user_stats[user_id]['total'] += 1
    if any(x in status for x in ['CHARGE', 'APPROVED', 'succeeded', 'accessToken']): user_stats[user_id]['charged'] += 1
    elif any(x in status for x in ['insufficient', 'Funds', 'INSUFFICIENT']): user_stats[user_id]['funds'] += 1
    elif any(x in status for x in ['security', 'CCN', 'INVALID_SECURITY_CODE']): user_stats[user_id]['ccn'] += 1
    else: user_stats[user_id]['declined'] += 1

def get_stats_text(user_id):
    if user_id not in user_stats: return f"<b>{em('error')} No stats yet</b>"
    s = user_stats[user_id]
    return f"<b>{em('stats')} YOUR STATS\n{em('charged')} Charged: {s['charged']}\n{em('funds')} Funds: {s['funds']}\n{em('ccn')} CCN: {s['ccn']}\n{em('declined')} Declined: {s['declined']}\n{em('gateway')} Total: {s['total']}</b>"

def get_user_status(user_id):
    if str(user_id) == str(ADMIN_ID): return f"{em('crown')} ADMIN"
    if is_user_premium(user_id):
        code = get_user_code(user_id)
        if code:
            expiry = user_codes.get(code, {}).get('expiry')
            if expiry:
                days_left = (expiry - datetime.now()).days
                return f"{em('star')} PREMIUM ({days_left} days)"
        return f"{em('star')} PREMIUM"
    return f"{em('lock')} FREE"

# ═══════════════════════════════════════════════════════════════
# تنسيق مخرجات البطاقة
# ═══════════════════════════════════════════════════════════════

def format_card_result(cc, gateway_name, gateway_cmd, result, elapsed, bin_info=""):
    status = "APPROVED" if "APPROVED" in result or "CHARGE" in result else "CCN" if "CCN" in result else "DECLINED"
    status_emoji = "✅" if status == "APPROVED" else "⚠️" if status == "CCN" else "❌"
    text = f"<b>[ϟ] Gateway: {gateway_name} [ {gateway_cmd} ]\n-------------------------------\n[ϟ] Card: <code>{cc}</code> {GATEWAYS.get(gateway_cmd.replace('/',''), {}).get('color', '🔥')}\n[ϟ] Status: {status}! {status_emoji}\n[ϟ] Response: {result}\n-------------------------------\n{bin_info}\n-------------------------------\n[ϟ] Time: {elapsed:.2f}s ⏱\n[ϟ] Price: {GATEWAYS.get(gateway_cmd.replace('/',''), {}).get('price', '$0.00')}\n[ϟ] By: {BOT_NAME}\n-------------------------------\n[ϟ] Dev: {DEVELOPER_USERNAME} - 💀</b>"
    return text, status

# ═══════════════════════════════════════════════════════════════
# 1. /iban - توليد IBAN وهمي
# ═══════════════════════════════════════════════════════════════

def generate_iban(country='DE'):
    iban_lengths = {'DE': 22, 'GB': 22, 'FR': 27, 'ES': 24, 'IT': 27, 'NL': 18, 'BE': 16, 'AT': 20, 'CH': 21, 'US': 0}
    length = iban_lengths.get(country, 22)
    if country == 'US': return "US doesn't use IBAN"
    bban = ''.join([str(random.randint(0, 9)) for _ in range(length - 4)])
    check_digits = str(random.randint(10, 99))
    return f"{country}{check_digits}{bban}"

@bot.message_handler(commands=['iban'])
def iban_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} Banned.</b>", parse_mode="HTML")
        return
    parts = message.text.split()
    country = parts[1].upper() if len(parts) > 1 else 'DE'
    iban = generate_iban(country)
    name = faker.name()
    bank = faker.company()
    text = f"<b>{em('iban')} IBAN GENERATOR\n\n{em('identity')} Name: <code>{name}</code>\n{em('iban')} IBAN: <code>{iban}</code>\n{em('world')} Country: {country}\n{em('bank')} Bank: {bank}\n\n{em('code')} Usage: <code>/iban DE</code> or <code>/iban GB</code></b>"
    bot.reply_to(message, text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 2. /identity - توليد هوية كاملة
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['identity'])
def identity_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} Banned.</b>", parse_mode="HTML")
        return
    country = message.text.split()[1] if len(message.text.split()) > 1 else 'US'
    fake = Faker(country.lower()) if country.lower() != 'us' else faker
    name = fake.name()
    address = fake.address().replace('\n', ', ')
    phone = fake.phone_number()
    email = fake.email()
    ssn = fake.ssn() if hasattr(fake, 'ssn') else 'N/A'
    dob = fake.date_of_birth(minimum_age=18, maximum_age=65).strftime('%d/%m/%Y')
    text = f"<b>{em('identity')} IDENTITY GENERATOR\n\n{em('identity')} Name: <code>{name}</code>\n📅 DOB: <code>{dob}</code>\n📧 Email: <code>{email}</code>\n📱 Phone: <code>{phone}</code>\n🏠 Address: <code>{address}</code>\n🔢 SSN: <code>{ssn}</code>\n\n{em('code')} Usage: <code>/identity US</code> or <code>/identity GB</code></b>"
    bot.reply_to(message, text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 3. /proxy - فحص البروكسي
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['proxy'])
def proxy_check_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} Banned.</b>", parse_mode="HTML")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"<b>{em('error')} Usage: <code>/proxy ip:port</code></b>", parse_mode="HTML")
        return
    proxy = parts[1]
    proxy_dict = parse_proxy(proxy)
    if not proxy_dict:
        bot.reply_to(message, f"<b>{em('error')} Invalid proxy format</b>", parse_mode="HTML")
        return
    msg = bot.reply_to(message, f"<b>{em('speed')} Checking proxy...</b>", parse_mode="HTML")
    try:
        start = time.time()
        r = requests.get('https://httpbin.org/ip', proxies=proxy_dict, timeout=10)
        elapsed = time.time() - start
        if r.status_code == 200:
            ip_data = r.json().get('origin', 'Unknown')
            bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('proxy')} PROXY ALIVE ✅\n\n<code>{proxy}</code>\n\n🌍 IP: <code>{ip_data}</code>\n⏱️ Speed: {elapsed:.2f}s</b>", parse_mode="HTML")
        else:
            bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('declined')} PROXY DEAD ❌\n\n<code>{proxy}</code>\n\nStatus: {r.status_code}</b>", parse_mode="HTML")
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('declined')} PROXY DEAD ❌\n\n<code>{proxy}</code>\n\nError: {str(e)[:50]}</b>", parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 4. /mass - فحص مجموعة بطاقات
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['mass'])
def mass_check_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} Banned.</b>", parse_mode="HTML")
        return
    if not is_user_premium(user_id):
        bot.reply_to(message, f"<b>{em('error')} Premium only.\n\n{em('star')} Use /stars to subscribe</b>", parse_mode="HTML")
        return
    parts = message.text.split('\n', 1)
    if len(parts) < 2:
        text = f"<b>{em('error')} Usage:\n<code>/mass\n4405...|10|2026|604\n4405...|11|2027|605</code></b>"
        bot.reply_to(message, text, parse_mode="HTML")
        return
    cards_text = parts[1]
    cards = extract_cc(cards_text)
    if not cards:
        bot.reply_to(message, f"<b>{em('error')} No valid cards found.</b>", parse_mode="HTML")
        return
    max_cards = MASS_CONFIG['premium_max_cards'] if is_user_premium(user_id) else MASS_CONFIG['free_max_cards']
    if len(cards) > max_cards:
        bot.reply_to(message, f"<b>{em('error')} Max {max_cards} cards. You sent {len(cards)}.</b>", parse_mode="HTML")
        return
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🟢 Approved 0", callback_data="mass_approved"))
    markup.add(InlineKeyboardButton("🔵 3D Secure 0", callback_data="mass_3d"))
    markup.add(InlineKeyboardButton("🔴 Declined 0", callback_data="mass_declined"))
    markup.add(InlineKeyboardButton("⏹ Stop", callback_data="mass_stop"))
    msg = bot.send_message(message.chat.id, f"<b>{em('mass')} MASS CHECK\n\n📁 Stripe Auth Mass Check\n⭐ Your Plan: {'Premium' if is_user_premium(user_id) else 'Free'}\n📊 Max Cards: {max_cards}\n💳 Format: 4111111111111111|12|2028|123\n✅ One card per line\n\n⏳ Checking {len(cards)} cards...</b>", reply_markup=markup, parse_mode="HTML")
    results = {'approved': [], 'ccn': [], 'declined': [], 'total': len(cards)}
    session_id = f"{user_id}_{int(time.time())}"
    mass_sessions[session_id] = {'active': True, 'msg_id': msg.message_id, 'chat_id': message.chat.id}
    for i, card in enumerate(cards):
        if not mass_sessions.get(session_id, {}).get('active', False):
            break
        try:
            result = xst_stripe_ezy(card)
            if "APPROVED" in result: results['approved'].append(card)
            elif "CCN" in result: results['ccn'].append(card)
            else: results['declined'].append(card)
            if (i + 1) % MASS_CONFIG['show_progress_every'] == 0 or i == len(cards) - 1:
                markup = InlineKeyboardMarkup(row_width=1)
                markup.add(InlineKeyboardButton(f"🟢 Approved {len(results['approved'])}", callback_data="mass_approved"))
                markup.add(InlineKeyboardButton(f"🔵 3D Secure {len(results['ccn'])}", callback_data="mass_3d"))
                markup.add(InlineKeyboardButton(f"🔴 Declined {len(results['declined'])}", callback_data="mass_declined"))
                markup.add(InlineKeyboardButton("⏹ Stop", callback_data=f"mass_stop_{session_id}"))
                try:
                    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('mass')} MASS CHECK PROGRESS\n\n📁 Stripe Auth Mass Check\n⭐ Your Plan: {'Premium' if is_user_premium(user_id) else 'Free'}\n📊 Max Cards: {max_cards}\n💳 Format: 4111111111111111|12|2028|123\n✅ One card per line\n\n✅ Will check first {len(cards)} cards\n\n💳 Card: {card}\n📊 Response: {result[:40]}...\n\n🟢 Approved: {len(results['approved'])}\n🔵 3D Secure: {len(results['ccn'])}\n🔴 Declined: {len(results['declined'])}\n📊 Total: {i+1}/{len(cards)}</b>", reply_markup=markup, parse_mode="HTML")
                except: pass
            time.sleep(MASS_CONFIG['delay_between_cards'])
        except Exception as e:
            results['declined'].append(card)
    mass_sessions[session_id]['active'] = False
    if user_id not in successful_cards: successful_cards[user_id] = []
    successful_cards[user_id].extend(results['approved'])
    successful_cards[user_id].extend(results['ccn'])
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(f"🟢 Approved {len(results['approved'])}", callback_data="mass_approved"))
    markup.add(InlineKeyboardButton(f"🔵 3D Secure {len(results['ccn'])}", callback_data="mass_3d"))
    markup.add(InlineKeyboardButton(f"🔴 Declined {len(results['declined'])}", callback_data="mass_declined"))
    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('mass')} MASS CHECK COMPLETE\n\n📁 Stripe Auth Mass Check\n⭐ Your Plan: {'Premium' if is_user_premium(user_id) else 'Free'}\n📊 Max Cards: {max_cards}\n\n🟢 Approved: {len(results['approved'])}\n🔵 3D Secure: {len(results['ccn'])}\n🔴 Declined: {len(results['declined'])}\n📊 Total: {len(cards)}\n\n💀 By: {BOT_NAME}</b>", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('mass_stop_'))
def mass_stop_callback(call):
    bot.answer_callback_query(call.id)
    session_id = call.data.replace('mass_stop_', '')
    if session_id in mass_sessions: mass_sessions[session_id]['active'] = False
    bot.send_message(call.message.chat.id, f"<b>{em('stop')} Mass check stopped.</b>", parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 5. /stats - إحصائيات المستخدم
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['stats'])
def stats_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} Banned.</b>", parse_mode="HTML")
        return
    bot.reply_to(message, get_stats_text(user_id), parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 6. /ping - فحص سرعة البوت
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['ping'])
def ping_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} Banned.</b>", parse_mode="HTML")
        return
    start = time.time()
    msg = bot.reply_to(message, f"<b>{em('ping')} PING...</b>", parse_mode="HTML")
    elapsed = (time.time() - start) * 1000
    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('ping')} PONG! ⚡\n\n⏱️ Latency: {elapsed:.1f}ms\n{em('status_icon')} Bot: Online\n{em('version_icon')} Version: {VERSION}</b>", parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 7. /export - تصدير البطاقات الناجحة
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['export'])
def export_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} Banned.</b>", parse_mode="HTML")
        return
    if user_id not in successful_cards or not successful_cards[user_id]:
        bot.reply_to(message, f"<b>{em('error')} No successful cards yet.</b>", parse_mode="HTML")
        return
    filename = f"hits_{user_id}_{int(time.time())}.txt"
    with open(filename, 'w') as f:
        f.write(f"Profesor Checker v{VERSION} - Exported Hits\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        for card in successful_cards[user_id]:
            f.write(f"{card}\n")
    with open(filename, 'rb') as f:
        bot.send_document(message.chat.id, f, caption=f"<b>{em('export')} EXPORTED HITS\n\n{em('charged')} Total: {len(successful_cards[user_id])}</b>", parse_mode="HTML")
    try: os.remove(filename)
    except: pass

# ═══════════════════════════════════════════════════════════════
# 8. /bin - معلومات BIN مفصلة
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['bin'])
def bin_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} Banned.</b>", parse_mode="HTML")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"<b>{em('error')} Usage: <code>/bin 400271</code></b>", parse_mode="HTML")
        return
    bin_num = parts[1][:6]
    msg = bot.reply_to(message, f"<b>{em('bin')} Loading BIN info...</b>", parse_mode="HTML")
    try:
        r = requests.get(f"https://bins.antipublic.cc/bins/{bin_num}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            text = f"<b>{em('bin')} BIN LOOKUP\n\n🔢 BIN: <code>{bin_num}</code>\n💳 Brand: {data.get('brand', '-')}\n📊 Type: {data.get('type', '-')}\n⭐ Level: {data.get('level', '-')}\n🏦 Bank: {data.get('bank', '-')}\n🌍 Country: {data.get('country_name', '-')} {data.get('country_flag', '')}\n\n{em('code')} Usage: <code>/bin {bin_num}</code></b>"
        else:
            text = f"<b>{em('error')} BIN not found.</b>"
    except Exception as e:
        text = f"<b>{em('error')} Error: {str(e)[:50]}</b>"
    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 9. /fake - توليد بيانات وهمية كاملة
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['fake'])
def fake_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} Banned.</b>", parse_mode="HTML")
        return
    country = message.text.split()[1] if len(message.text.split()) > 1 else 'US'
    fake = Faker(country.lower()) if country.lower() != 'us' else faker
    cc = fake.credit_card_full()
    name = fake.name()
    address = fake.address()
    phone = fake.phone_number()
    email = fake.email()
    company = fake.company()
    job = fake.job()
    text = f"<b>{em('fake')} FAKE DATA GENERATOR\n\n{em('identity')} Name: <code>{name}</code>\n💼 Job: <code>{job}</code>\n🏢 Company: <code>{company}</code>\n📧 Email: <code>{email}</code>\n📱 Phone: <code>{phone}</code>\n🏠 Address:\n<code>{address}</code>\n\n💳 Credit Card:\n<code>{cc}</code>\n\n{em('code')} Usage: <code>/fake US</code> or <code>/fake GB</code></b>"
    bot.reply_to(message, text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 10. /check - فحص على كل البوابات
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['check'])
def check_all_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} Banned.</b>", parse_mode="HTML")
        return
    if not is_user_premium(user_id):
        bot.reply_to(message, f"<b>{em('error')} Premium only.\n\n{em('star')} Use /stars to subscribe</b>", parse_mode="HTML")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"<b>{em('error')} Usage: <code>/check 4405103045656027|10|2026|604</code></b>", parse_mode="HTML")
        return
    cc = reg(parts[1])
    if not cc:
        bot.reply_to(message, f"<b>{em('error')} Invalid card format.</b>", parse_mode="HTML")
        return
    msg = bot.reply_to(message, f"<b>{em('check')} Checking all gateways...</b>", parse_mode="HTML")
    gateways = [("Stripe 0.00$", xst_stripe_ezy, "stripe", "/st"), ("Payments.AI", xst_payments_ai, "paymentsai", "/pa"), ("Braintree", xst_bt_dna, "braintree", "/bt"), ("PayPal 7$", xst_paypal_brass, "paypal", "/pp")]
    results_text = f"<b>{em('check')} ALL GATEWAYS CHECK\n\n💳 Card: <code>{cc}</code>\n\n"
    for name, func, emoji_key, cmd in gateways:
        try:
            start = time.time()
            result = func(cc)
            elapsed = time.time() - start
            status = "✅" if "APPROVED" in result or "CHARGE" in result else "⚠️" if "CCN" in result else "❌"
            results_text += f"{em(emoji_key)} {name}: {status}\n⏱️ {elapsed:.1f}s | {result[:40]}\n\n"
            if "APPROVED" in result or "CHARGE" in result:
                if user_id not in successful_cards: successful_cards[user_id] = []
                successful_cards[user_id].append(f"{cc} | {name}")
        except Exception as e:
            results_text += f"{em(emoji_key)} {name}: ❌\nError: {str(e)[:30]}\n\n"
    results_text += f"💀 By: {BOT_NAME}</b>"
    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=results_text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# نظام الدفع بالنجوم (Telegram Stars)
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['stars'])
def stars_menu(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} Banned.</b>", parse_mode="HTML")
        return
    markup = InlineKeyboardMarkup(row_width=1)
    for key, plan in STARS_PRICES.items():
        markup.add(InlineKeyboardButton(f"〔 {plan['label']} - {plan['price']} ⭐ 〕", callback_data=f"stars_buy_{key}"))
    markup.add(InlineKeyboardButton("〔 🔙 Return 〕", callback_data="menu_back"))
    text = f"<b>{em('star')} STARS PAYMENT SYSTEM\n\n{em('crown')} Choose a subscription plan:\n\n{em('star')} 1 Day - 1 ⭐\n{em('star')} 1 Week - 5 ⭐\n{em('star')} 1 Month - 15 ⭐\n{em('star')} 3 Months - 40 ⭐\n{em('star')} 6 Months - 70 ⭐\n{em('star')} 1 Year - 120 ⭐\n\n{em('choose')} Click on the desired plan</b>"
    bot.send_photo(message.chat.id, BANNER_URL, caption=text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('stars_buy_'))
def stars_buy_callback(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    plan_key = call.data.replace('stars_buy_', '')
    if plan_key not in STARS_PRICES:
        bot.send_message(call.message.chat.id, f"<b>{em('error')} Invalid plan</b>", parse_mode="HTML")
        return
    plan = STARS_PRICES[plan_key]
    prices = [LabeledPrice(label=f"Subscription {plan['label']}", amount=plan['price'])]
    bot.send_invoice(chat_id=call.message.chat.id, title=f"Profesor Checker - {plan['label']}", description=f"Subscription with {plan['price']} stars ⭐ for {plan['label']}", invoice_payload=f"stars_{plan_key}_{user_id}_{int(time.time())}", provider_token="", currency="XTR", prices=prices, start_parameter=f"stars_{plan_key}", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(f"〔 Pay {plan['price']} ⭐ 〕", pay=True)))

@bot.pre_checkout_query_handler(func=lambda query: True)
def stars_pre_checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def stars_successful_payment(message):
    user_id = str(message.from_user.id)
    payload = message.successful_payment.invoice_payload
    try:
        parts = payload.split('_')
        plan_key = parts[1]
        plan = STARS_PRICES[plan_key]
        expiry = datetime.now() + timedelta(days=plan['days'])
        code = f"STARS-{user_id}-{int(time.time())}"
        user_codes[code] = {'user_id': user_id, 'expiry': expiry, 'type': 'stars', 'plan': plan_key, 'price': plan['price']}
        text = f"<b>{em('success')} PAYMENT SUCCESSFUL!\n\n{em('star')} Payment completed!\n{em('time')} Duration: {plan['label']}\n{em('calendar')} Expires: {expiry.strftime('%Y-%m-%d %H:%M')}\n{em('unlock')} Status: PREMIUM\n\n{em('fire')} You can now use all features!</b>"
        bot.send_message(message.chat.id, text, parse_mode="HTML")
        try:
            admin_text = f"<b>{em('star')} NEW STARS PAYMENT\n\n👤 User ID: <code>{user_id}</code>\n📦 Plan: {plan['label']}\n⭐ Stars: {plan['price']}\n📅 Expiry: {expiry.strftime('%Y-%m-%d')}\n\n{em('money')} Stars transferred to your account automatically!</b>"
            bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
        except: pass
    except Exception as e:
        bot.send_message(message.chat.id, f"<b>{em('error')} Payment processing error: {str(e)[:50]}</b>", parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# START + القائمة الرئيسية
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} You are banned.</b>", parse_mode="HTML")
        return
    if user_id != str(ADMIN_ID) and not is_user_premium(user_id) and user_id not in pending_activation:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("〔 Request Activation 〕", callback_data="request_activation"))
        markup.add(InlineKeyboardButton("〔 ⭐ Subscribe with Stars 〕", callback_data="stars_menu"))
        text = f"<b>{em('welcome')} WELCOME TO {BOT_NAME}\n\n{em('declined')} ACCESS DENIED\n{em('error')} You need an activation code.\n\n{em('choose')} Choose activation method:</b>"
        bot.send_photo(message.chat.id, BANNER_URL, caption=text, reply_markup=markup, parse_mode="HTML")
        return
    name = message.from_user.first_name
    if user_id not in user_stats: user_stats[user_id] = {'total': 0, 'charged': 0, 'funds': 0, 'ccn': 0, 'declined': 0}
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("〔 Tools 〕", callback_data="menu_tools"), InlineKeyboardButton("〔 Proxy 〕", callback_data="menu_proxy"))
    markup.add(InlineKeyboardButton("〔 New Commands 〕", callback_data="menu_new"), InlineKeyboardButton("〔 Dev 〕", callback_data="menu_dev"))
    markup.add(InlineKeyboardButton("〔 ⭐ Subscribe with Stars 〕", callback_data="stars_menu"), InlineKeyboardButton("〔 Profile 〕", callback_data="menu_profile"))
    status = get_user_status(user_id)
    text = f"<b>✦ WELCOME {name} TO {BOT_NAME} ✦\n\n【{em('gateway')}】 GATEWAYS ➛ Stripe + Braintree + PayPal + Payments.AI\n【{em('mode')}】 MODE ➛ Auth + Charge\n【{em('speed')}】 SPEED ➛ Ultra Fast\n【{em('status_icon')}】 STATUS ➛ {status}\n【{em('version_icon')}】 VERSION ➛ {VERSION}\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n【「{em('choose')}」】 CHOOSE A SERVICE 【「{em('choose')}」】</b>"
    bot.send_photo(message.chat.id, BANNER_URL, caption=text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'stars_menu')
def stars_menu_callback(call):
    bot.answer_callback_query(call.id)
    stars_menu(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'request_activation')
def request_activation_callback(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    username = call.from_user.username or "N/A"
    if user_id in pending_activation:
        bot.send_message(call.message.chat.id, f"<b>{em('error')} You already sent a request, please wait.</b>", parse_mode="HTML")
        return
    pending_activation[user_id] = {'time': datetime.now(), 'username': username}
    try:
        admin_text = f"<b>{em('admin_icon')} NEW ACTIVATION REQUEST\n\n👤 User ID: <code>{user_id}</code>\n📛 Username: @{username}\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{em('code')} To approve:\n<code>/approve {user_id} 7</code> (7 days)\n<code>/approve {user_id} 30</code> (30 days)</b>"
        admin_markup = InlineKeyboardMarkup(row_width=2)
        admin_markup.add(InlineKeyboardButton("〔 ✅ Approve 7 days 〕", callback_data=f"approve_{user_id}_7"), InlineKeyboardButton("〔 ✅ Approve 30 days 〕", callback_data=f"approve_{user_id}_30"))
        admin_markup.add(InlineKeyboardButton("〔 ❌ Reject 〕", callback_data=f"reject_{user_id}"))
        bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_markup, parse_mode="HTML")
    except Exception as e:
        print(f"Error notifying admin: {e}")
    bot.send_message(call.message.chat.id, f"<b>{em('success')} Activation request sent to admin.\n{em('time')} Please wait...\n\n{em('star')} Or subscribe with stars immediately via /stars</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
def approve_callback(call):
    bot.answer_callback_query(call.id)
    if str(call.from_user.id) != str(ADMIN_ID):
        bot.send_message(call.message.chat.id, f"<b>{em('error')} Not authorized!</b>", parse_mode="HTML")
        return
    parts = call.data.split('_')
    user_id = parts[1]
    days = int(parts[2]) if len(parts) > 2 else 7
    code = generate_code()
    expiry = datetime.now() + timedelta(days=days)
    user_codes[code] = {'user_id': user_id, 'expiry': expiry, 'type': 'admin'}
    try:
        user_text = f"<b>{em('success')} ACTIVATION APPROVED!\n\n{em('code')} Your Code: <code>{code}</code>\n{em('time')} Valid until: {expiry.strftime('%Y-%m-%d %H:%M')}\n{em('unlock')} Status: PREMIUM\n\n{em('fire')} Send /start to access!</b>"
        bot.send_message(user_id, user_text, parse_mode="HTML")
    except: pass
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"<b>{em('success')} User {user_id} approved\n{em('code')} Code: <code>{code}</code>\n{em('time')} Valid for {days} days</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def reject_callback(call):
    bot.answer_callback_query(call.id)
    if str(call.from_user.id) != str(ADMIN_ID):
        bot.send_message(call.message.chat.id, f"<b>{em('error')} Not authorized!</b>", parse_mode="HTML")
        return
    user_id = call.data.split('_')[1]
    try:
        bot.send_message(user_id, f"<b>{em('declined')} Activation request rejected.\n{em('star')} You can subscribe with stars via /stars</b>", parse_mode="HTML")
    except: pass
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"<b>{em('declined')} User {user_id} rejected</b>", parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# قائمة الأوامر الجديدة
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data == 'menu_new')
def menu_new(call):
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("〔 IBAN 〕", callback_data="cmd_iban"), InlineKeyboardButton("〔 Identity 〕", callback_data="cmd_identity"))
    markup.add(InlineKeyboardButton("〔 Proxy Chk 〕", callback_data="cmd_proxy"), InlineKeyboardButton("〔 Mass 〕", callback_data="cmd_mass"))
    markup.add(InlineKeyboardButton("〔 Stats 〕", callback_data="cmd_stats"), InlineKeyboardButton("〔 Ping 〕", callback_data="cmd_ping"))
    markup.add(InlineKeyboardButton("〔 Export 〕", callback_data="cmd_export"), InlineKeyboardButton("〔 BIN 〕", callback_data="cmd_bin"))
    markup.add(InlineKeyboardButton("〔 Fake 〕", callback_data="cmd_fake"), InlineKeyboardButton("〔 Check All 〕", callback_data="cmd_check"))
    markup.add(InlineKeyboardButton("〔 🔙 Back 〕", callback_data="menu_back"))
    text = f"<b>{em('tools')} NEW COMMANDS MENU\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n{em('iban')} /iban - Generate fake IBAN\n{em('identity')} /identity - Generate full identity\n{em('proxy')} /proxy - Check proxy status\n{em('mass')} /mass - Mass card check\n{em('stats')} /stats - Your statistics\n{em('ping')} /ping - Bot speed test\n{em('export')} /export - Export hits\n{em('bin')} /bin - BIN lookup\n{em('fake')} /fake - Generate fake data\n{em('check')} /check - Check all gateways\n\n{em('choose')} Select a command</b>"
    bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id, media=InputMediaPhoto(BANNER_URL, caption=text, parse_mode='HTML'), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cmd_'))
def cmd_callbacks(call):
    bot.answer_callback_query(call.id)
    cmd = call.data.replace('cmd_', '')
    examples = {'iban': '/iban DE\n/iban GB\n/iban FR', 'identity': '/identity US\n/identity GB\n/identity DE', 'proxy': '/proxy 1.2.3.4:8080\n/proxy 1.2.3.4:8080:user:pass', 'mass': '/mass\n4405...|10|2026|604\n4405...|11|2027|605', 'stats': '/stats', 'ping': '/ping', 'export': '/export', 'bin': '/bin 400271\n/bin 515676', 'fake': '/fake US\n/fake GB\n/fake DE', 'check': '/check 4405103045656027|10|2026|604'}
    text = f"<b>{em(cmd)} COMMAND: /{cmd}\n\n{em('code')} Usage:\n<code>{examples.get(cmd, '/' + cmd)}</code>\n\n{em('choose')} Send the command in chat</b>"
    bot.send_message(call.message.chat.id, text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# قائمة الأدوات
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data == 'menu_tools')
def menu_tools(call):
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("〔 Stripe 〕", callback_data="check_stripe_ezy"), InlineKeyboardButton("〔 Payments.AI 〕", callback_data="check_payments_ai"))
    markup.add(InlineKeyboardButton("〔 Braintree 〕", callback_data="check_braintree"), InlineKeyboardButton("〔 PayPal 7$ 〕", callback_data="check_paypal"))
    markup.add(InlineKeyboardButton("〔 🔙 Back 〕", callback_data="menu_back"))
    text = f"<b>{em('tools')} TOOLS MENU\n━━━━━━━━━━━━━━━━━━━━━━━━\n{em('choose')} Select a gateway to check card</b>"
    bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id, media=InputMediaPhoto(BANNER_URL, caption=text, parse_mode='HTML'), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'menu_back')
def menu_back(call):
    bot.answer_callback_query(call.id)
    name = call.from_user.first_name
    user_id = str(call.from_user.id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("〔 Tools 〕", callback_data="menu_tools"), InlineKeyboardButton("〔 Proxy 〕", callback_data="menu_proxy"))
    markup.add(InlineKeyboardButton("〔 New Commands 〕", callback_data="menu_new"), InlineKeyboardButton("〔 Dev 〕", callback_data="menu_dev"))
    markup.add(InlineKeyboardButton("〔 ⭐ Subscribe with Stars 〕", callback_data="stars_menu"), InlineKeyboardButton("〔 Profile 〕", callback_data="menu_profile"))
    status = get_user_status(user_id)
    text = f"<b>✦ WELCOME {name} TO {BOT_NAME} ✦\n\n【{em('gateway')}】 GATEWAYS ➛ Stripe + Braintree + PayPal + Payments.AI\n【{em('mode')}】 MODE ➛ Auth + Charge\n【{em('speed')}】 SPEED ➛ Ultra Fast\n【{em('status_icon')}】 STATUS ➛ {status}\n【{em('version_icon')}】 VERSION ➛ {VERSION}\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n【「{em('choose')}」】 CHOOSE A SERVICE 【「{em('choose')}」】</b>"
    bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id, media=InputMediaPhoto(BANNER_URL, caption=text, parse_mode='HTML'), reply_markup=markup)

# ═══════════════════════════════════════════════════════════════
# معالجات فحص البوابات الفردية
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data == 'check_stripe_ezy')
def check_stripe_ezy_callback(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    if not is_user_premium(user_id):
        bot.send_message(call.message.chat.id, f"<b>{em('error')} Premium only.\n\n{em('star')} Use /stars to subscribe</b>", parse_mode="HTML")
        return
    bot.send_message(call.message.chat.id, f"<b>{em('stripe')} Send card in format:\n<code>4405103045656027|10|2026|604</code></b>", parse_mode="HTML")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, stripe_check_handler)

def stripe_check_handler(message):
    user_id = str(message.from_user.id)
    cc = reg(message.text)
    if not cc:
        bot.reply_to(message, f"<b>{em('error')} Invalid card format.</b>", parse_mode="HTML")
        return
    msg = bot.reply_to(message, f"<b>{em('stripe')} Checking Stripe...</b>", parse_mode="HTML")
    try:
        start = time.time()
        result = xst_stripe_ezy(cc)
        elapsed = time.time() - start
        update_stats(user_id, result)
        bin_num = cc.split('|')[0][:6]
        bin_info = dato(bin_num)
        text, status = format_card_result(cc, "Stripe 0.00$", "/st", result, elapsed, bin_info)
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=text, parse_mode="HTML")
        if status == "APPROVED":
            if user_id not in successful_cards: successful_cards[user_id] = []
            successful_cards[user_id].append(f"{cc} | Stripe")
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('error')} Error: {str(e)[:50]}</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'check_payments_ai')
def check_payments_ai_callback(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    if not is_user_premium(user_id):
        bot.send_message(call.message.chat.id, f"<b>{em('error')} Premium only.\n\n{em('star')} Use /stars to subscribe</b>", parse_mode="HTML")
        return
    bot.send_message(call.message.chat.id, f"<b>{em('paymentsai')} Send card in format:\n<code>4405103045656027|10|2026|604</code></b>", parse_mode="HTML")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, payments_ai_check_handler)

def payments_ai_check_handler(message):
    user_id = str(message.from_user.id)
    cc = reg(message.text)
    if not cc:
        bot.reply_to(message, f"<b>{em('error')} Invalid card format.</b>", parse_mode="HTML")
        return
    msg = bot.reply_to(message, f"<b>{em('paymentsai')} Checking Payments.AI...</b>", parse_mode="HTML")
    try:
        start = time.time()
        result = xst_payments_ai(cc)
        elapsed = time.time() - start
        update_stats(user_id, result)
        bin_num = cc.split('|')[0][:6]
        bin_info = dato(bin_num)
        text, status = format_card_result(cc, "Payments.AI", "/pa", result, elapsed, bin_info)
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=text, parse_mode="HTML")
        if status == "APPROVED":
            if user_id not in successful_cards: successful_cards[user_id] = []
            successful_cards[user_id].append(f"{cc} | Payments.AI")
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('error')} Error: {str(e)[:50]}</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'check_braintree')
def check_braintree_callback(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    if not is_user_premium(user_id):
        bot.send_message(call.message.chat.id, f"<b>{em('error')} Premium only.\n\n{em('star')} Use /stars to subscribe</b>", parse_mode="HTML")
        return
    bot.send_message(call.message.chat.id, f"<b>{em('braintree')} Send card in format:\n<code>4405103045656027|10|2026|604</code></b>", parse_mode="HTML")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, braintree_check_handler)

def braintree_check_handler(message):
    user_id = str(message.from_user.id)
    cc = reg(message.text)
    if not cc:
        bot.reply_to(message, f"<b>{em('error')} Invalid card format.</b>", parse_mode="HTML")
        return
    msg = bot.reply_to(message, f"<b>{em('braintree')} Checking Braintree...</b>", parse_mode="HTML")
    try:
        start = time.time()
        result = xst_bt_dna(cc)
        elapsed = time.time() - start
        update_stats(user_id, result)
        bin_num = cc.split('|')[0][:6]
        bin_info = dato(bin_num)
        text, status = format_card_result(cc, "Braintree", "/bt", result, elapsed, bin_info)
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=text, parse_mode="HTML")
        if status == "APPROVED":
            if user_id not in successful_cards: successful_cards[user_id] = []
            successful_cards[user_id].append(f"{cc} | Braintree")
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('error')} Error: {str(e)[:50]}</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'check_paypal')
def check_paypal_callback(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    if not is_user_premium(user_id):
        bot.send_message(call.message.chat.id, f"<b>{em('error')} Premium only.\n\n{em('star')} Use /stars to subscribe</b>", parse_mode="HTML")
        return
    bot.send_message(call.message.chat.id, f"<b>{em('paypal')} Send card in format:\n<code>4405103045656027|10|2026|604</code></b>", parse_mode="HTML")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, paypal_check_handler)

def paypal_check_handler(message):
    user_id = str(message.from_user.id)
    cc = reg(message.text)
    if not cc:
        bot.reply_to(message, f"<b>{em('error')} Invalid card format.</b>", parse_mode="HTML")
        return
    msg = bot.reply_to(message, f"<b>{em('paypal')} Checking PayPal...</b>", parse_mode="HTML")
    try:
        start = time.time()
        result = xst_paypal_brass(cc)
        elapsed = time.time() - start
        update_stats(user_id, result)
        bin_num = cc.split('|')[0][:6]
        bin_info = dato(bin_num)
        text, status = format_card_result(cc, "PayPal 7$", "/pp", result, elapsed, bin_info)
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=text, parse_mode="HTML")
        if status == "APPROVED":
            if user_id not in successful_cards: successful_cards[user_id] = []
            successful_cards[user_id].append(f"{cc} | PayPal")
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('error')} Error: {str(e)[:50]}</b>", parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# أوامر أخرى ومعالجات
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data == 'menu_proxy')
def menu_proxy(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"<b>{em('proxy')} Send proxy in format:\n<code>ip:port</code> or <code>ip:port:user:pass</code></b>", parse_mode="HTML")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, proxy_handler)

def proxy_handler(message):
    proxy_str = message.text.strip()
    proxy = parse_proxy(proxy_str)
    if not proxy:
        bot.reply_to(message, f"<b>{em('error')} Invalid proxy format</b>", parse_mode="HTML")
        return
    add_user_proxy(str(message.from_user.id), proxy_str)
    bot.reply_to(message, f"<b>{em('success')} Proxy added:\n<code>{proxy_str}</code></b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'menu_dev')
def menu_dev(call):
    bot.answer_callback_query(call.id)
    text = f"<b>{em('developer')} DEVELOPER INFO\n\n💎 Dev: {DEVELOPER_USERNAME}\n🔧 Version: {VERSION}\n🚀 Gateways: Stripe + Payments.AI + Braintree + PayPal\n⭐ Stars Payment: Active\n\n💀 {BOT_NAME} v{VERSION}</b>"
    bot.send_message(call.message.chat.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'menu_profile')
def menu_profile(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    status = get_user_status(user_id)
    stats = get_stats_text(user_id)
    text = f"<b>{em('profile_icon')} YOUR PROFILE\n\n👤 User ID: <code>{user_id}</code>\n{status}\n\n{stats}\n\n💀 {BOT_NAME}</b>"
    bot.send_message(call.message.chat.id, text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# أوامر الأدمن
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['approve'])
def approve_command(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, f"<b>{em('error')} Admin only.</b>", parse_mode="HTML")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"<b>{em('error')} Usage: <code>/approve user_id days</code></b>", parse_mode="HTML")
        return
    user_id = parts[1]
    days = int(parts[2]) if len(parts) > 2 else 7
    code = generate_code()
    expiry = datetime.now() + timedelta(days=days)
    user_codes[code] = {'user_id': user_id, 'expiry': expiry, 'type': 'admin'}
    try:
        user_text = f"<b>{em('success')} ACTIVATION APPROVED!\n\n{em('code')} Your Code: <code>{code}</code>\n{em('time')} Valid until: {expiry.strftime('%Y-%m-%d %H:%M')}\n{em('unlock')} Status: PREMIUM\n\n{em('fire')} Send /start to access!</b>"
        bot.send_message(user_id, user_text, parse_mode="HTML")
    except: pass
    bot.reply_to(message, f"<b>{em('success')} User {user_id} approved.\n{em('code')} Code: <code>{code}</code></b>", parse_mode="HTML")

@bot.message_handler(commands=['ban'])
def ban_command(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, f"<b>{em('error')} Admin only.</b>", parse_mode="HTML")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"<b>{em('error')} Usage: <code>/ban user_id</code></b>", parse_mode="HTML")
        return
    user_id = parts[1]
    if user_id not in banned_users: banned_users.append(user_id)
    bot.reply_to(message, f"<b>{em('success')} User {user_id} banned.</b>", parse_mode="HTML")

@bot.message_handler(commands=['unban'])
def unban_command(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, f"<b>{em('error')} Admin only.</b>", parse_mode="HTML")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"<b>{em('error')} Usage: <code>/unban user_id</code></b>", parse_mode="HTML")
        return
    user_id = parts[1]
    if user_id in banned_users: banned_users.remove(user_id)
    bot.reply_to(message, f"<b>{em('success')} User {user_id} unbanned.</b>", parse_mode="HTML")

@bot.message_handler(commands=['users'])
def users_command(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, f"<b>{em('error')} Admin only.</b>", parse_mode="HTML")
        return
    total_users = len(user_stats)
    premium_users = sum(1 for code, data in user_codes.items() if data.get('type') in ['admin', 'stars'] and datetime.now() < data.get('expiry', datetime.now()))
    banned_count = len(banned_users)
    text = f"<b>{em('admin_icon')} ADMIN STATS\n\n👥 Total Users: {total_users}\n⭐ Premium Users: {premium_users}\n🚫 Banned: {banned_count}\n🔑 Active Codes: {len(user_codes)}\n\n💀 {BOT_NAME} v{VERSION}</b>"
    bot.reply_to(message, text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# تشغيل البوت
# ═══════════════════════════════════════════════════════════════

print(f'✦ {BOT_NAME} {VERSION} Running...')
print(f'💎 Dev: {DEVELOPER_USERNAME}')
print(f'🚀 Gateways: Stripe + Payments.AI + Braintree + PayPal')
print(f'⭐ Stars Payment: Active (1 Star = 1 Day)')
print(f'🔥 New Commands: /iban /identity /proxy /mass /stats /ping /export /bin /fake /check /stars')

while True:
    try: bot.infinity_polling()
    except Exception as e: print(f'❌ Error: {e}'); time.sleep(5)
