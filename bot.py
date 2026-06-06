#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Mo.dark جاهز 🕷️☠️
# Profesor Checker v8.0 ULTIMATE

import telebot, requests, random, re, json, uuid, string, time, threading
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
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
    if user_id not in user_stats: return f"<b>{em('error')} 𝗡𝗼 𝘀𝘁𝗮𝘁𝘀 𝘆𝗲𝘁</b>"
    s = user_stats[user_id]
    return f"""<b>{em('stats')} 𝗬𝗢𝗨𝗥 𝗦𝗧𝗔𝗧𝗦
{em('charged')} 𝗖𝗵𝗮𝗿𝗴𝗲𝗱: {s['charged']}
{em('funds')} 𝗙𝘂𝗻𝗱𝘀: {s['funds']}
{em('ccn')} 𝗖𝗖𝗡: {s['ccn']}
{em('declined')} 𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱: {s['declined']}
{em('gateway')} 𝗧𝗼𝘁𝗮𝗹: {s['total']}</b>"""

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
        bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    parts = message.text.split()
    country = parts[1].upper() if len(parts) > 1 else 'DE'
    
    iban = generate_iban(country)
    name = faker.name()
    bank = faker.company()
    
    text = f"""<b>{em('iban')} 𝗜𝗕𝗔𝗡 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗢𝗥

{em('identity')} 𝗡𝗮𝗺𝗲: <code>{name}</code>
{em('iban')} 𝗜𝗕𝗔𝗡: <code>{iban}</code>
{em('world')} 𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country}
{em('bank')} 𝗕𝗮𝗻𝗸: {bank}

{em('code')} 𝗨𝘀𝗮𝗴𝗲: <code>/iban DE</code> or <code>/iban GB</code></b>"""
    
    bot.reply_to(message, text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 2. /identity - توليد هوية كاملة
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['identity'])
def identity_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    country = message.text.split()[1] if len(message.text.split()) > 1 else 'US'
    fake = Faker(country.lower()) if country.lower() != 'us' else faker
    
    name = fake.name()
    address = fake.address().replace('\n', ', ')
    phone = fake.phone_number()
    email = fake.email()
    ssn = fake.ssn() if hasattr(fake, 'ssn') else 'N/A'
    dob = fake.date_of_birth(minimum_age=18, maximum_age=65).strftime('%d/%m/%Y')
    
    text = f"""<b>{em('identity')} 𝗜𝗗𝗘𝗡𝗧𝗜𝗧𝗬 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗢𝗥

{em('identity')} 𝗡𝗮𝗺𝗲: <code>{name}</code>
📅 𝗗𝗢𝗕: <code>{dob}</code>
📧 𝗘𝗺𝗮𝗶𝗹: <code>{email}</code>
📱 𝗣𝗵𝗼𝗻𝗲: <code>{phone}</code>
🏠 𝗔𝗱𝗱𝗿𝗲𝘀𝘀: <code>{address}</code>
🔢 𝗦𝗦𝗡: <code>{ssn}</code>

{em('code')} 𝗨𝘀𝗮𝗴𝗲: <code>/identity US</code> or <code>/identity GB</code></b>"""
    
    bot.reply_to(message, text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 3. /proxy - فحص البروكسي
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['proxy'])
def proxy_check_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"<b>{em('error')} 𝗨𝘀𝗮𝗴𝗲: <code>/proxy ip:port</code></b>", parse_mode="HTML")
        return
    
    proxy = parts[1]
    proxy_dict = parse_proxy(proxy)
    
    if not proxy_dict:
        bot.reply_to(message, f"<b>{em('error')} 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗽𝗿𝗼𝘅𝘆 𝗳𝗼𝗿𝗺𝗮𝘁</b>", parse_mode="HTML")
        return
    
    msg = bot.reply_to(message, f"<b>{em('speed')} 𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗴 𝗽𝗿𝗼𝘅𝘆...</b>", parse_mode="HTML")
    
    try:
        start = time.time()
        r = requests.get('https://httpbin.org/ip', proxies=proxy_dict, timeout=10)
        elapsed = time.time() - start
        
        if r.status_code == 200:
            ip_data = r.json().get('origin', 'Unknown')
            bot.edit_message_text(
                chat_id=message.chat.id, message_id=msg.message_id,
                text=f"<b>{em('proxy')} 𝗣𝗥𝗢𝗫𝗬 𝗔𝗟𝗜𝗩𝗘 ✅\n\n<code>{proxy}</code>\n\n🌍 𝗜𝗣: <code>{ip_data}</code>\n⏱️ 𝗦𝗽𝗲𝗲𝗱: {elapsed:.2f}s</b>",
                parse_mode="HTML"
            )
        else:
            bot.edit_message_text(
                chat_id=message.chat.id, message_id=msg.message_id,
                text=f"<b>{em('declined')} 𝗣𝗥𝗢𝗫𝗬 𝗗𝗘𝗔𝗗 ❌\n\n<code>{proxy}</code>\n\n𝗦𝘁𝗮𝘁𝘂𝘀: {r.status_code}</b>",
                parse_mode="HTML"
            )
    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id, message_id=msg.message_id,
            text=f"<b>{em('declined')} 𝗣𝗥𝗢𝗫𝗬 𝗗𝗘𝗔𝗗 ❌\n\n<code>{proxy}</code>\n\n𝗘𝗿𝗿𝗼𝗿: {str(e)[:50]}</b>",
            parse_mode="HTML"
        )

# ═══════════════════════════════════════════════════════════════
# 4. /mass - فحص مجموعة بطاقات
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['mass'])
def mass_check_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    if not is_code_valid(get_user_code(user_id)) and str(user_id) != str(ADMIN_ID):
        bot.reply_to(message, f"<b>{em('error')} 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗼𝗻𝗹𝘆.</b>", parse_mode="HTML")
        return
    
    parts = message.text.split('\n', 1)
    if len(parts) < 2:
        bot.reply_to(message, f"<b>{em('error')} 𝗨𝘀𝗮𝗴𝗲:\n<code>/mass\n4405...|10|2026|604\n4405...|11|2027|605</code></b>", parse_mode="HTML")
        return
    
    cards_text = parts[1]
    cards = extract_cc(cards_text)
    
    if not cards:
        bot.reply_to(message, f"<b>{em('error')} 𝗡𝗼 𝘃𝗮𝗹𝗶𝗱 𝗰𝗮𝗿𝗱𝘀 𝗳𝗼𝘂𝗻𝗱.</b>", parse_mode="HTML")
        return
    
    if len(cards) > 20:
        bot.reply_to(message, f"<b>{em('error')} 𝗠𝗮𝘅 𝟮𝟬 𝗰𝗮𝗿𝗱𝘀. 𝗬𝗼𝘂 𝘀𝗲𝗻𝘁 {len(cards)}.</b>", parse_mode="HTML")
        return
    
    msg = bot.reply_to(message, f"<b>{em('mass')} 𝗠𝗔𝗦𝗦 𝗖𝗛𝗘𝗖𝗞\n\n⏳ Checking {len(cards)} cards...</b>", parse_mode="HTML")
    
    results = {'charged': [], 'approved': [], 'ccn': [], 'dead': []}
    
    for i, card in enumerate(cards):
        try:
            result = xst_stripe_ezy(card)
            status = "CHARGED" if "APPROVED" in result or "CHARGE" in result else "CCN" if "CCN" in result else "DEAD"
            
            if status == "CHARGED":
                results['charged'].append(card)
            elif status == "CCN":
                results['ccn'].append(card)
            else:
                results['dead'].append(card)
            
            time.sleep(2)
        except:
            results['dead'].append(card)
    
    # Save successful
    if user_id not in successful_cards:
        successful_cards[user_id] = []
    successful_cards[user_id].extend(results['charged'])
    successful_cards[user_id].extend(results['ccn'])
    
    text = f"""<b>{em('mass')} 𝗠𝗔𝗦𝗦 𝗖𝗛𝗘𝗖𝗞 𝗥𝗘𝗦𝗨𝗟𝗧𝗦

{em('charged')} 𝗖𝗵𝗮𝗿𝗴𝗲𝗱: {len(results['charged'])}
{em('ccn')} 𝗖𝗖𝗡: {len(results['ccn'])}
{em('declined')} 𝗗𝗲𝗮𝗱: {len(results['dead'])}
{em('gateway')} 𝗧𝗼𝘁𝗮𝗹: {len(cards)}

{em('charged')} 𝗟𝗶𝘃𝗲 𝗖𝗮𝗿𝗱𝘀:
{chr(10).join([f'<code>{c}</code>' for c in results['charged'][:5]])}</b>"""
    
    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 5. /stats - إحصائيات المستخدم
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['stats'])
def stats_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    bot.reply_to(message, get_stats_text(user_id), parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 6. /ping - فحص سرعة البوت
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['ping'])
def ping_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    start = time.time()
    msg = bot.reply_to(message, f"<b>{em('ping')} 𝗣𝗜𝗡𝗚...</b>", parse_mode="HTML")
    elapsed = (time.time() - start) * 1000
    
    bot.edit_message_text(
        chat_id=message.chat.id, message_id=msg.message_id,
        text=f"<b>{em('ping')} 𝗣𝗢𝗡𝗚! ⚡\n\n⏱️ 𝗟𝗮𝘁𝗲𝗻𝗰𝘆: {elapsed:.1f}ms\n{em('status_icon')} 𝗕𝗼𝘁: 𝗢𝗻𝗹𝗶𝗻𝗲\n{em('version_icon')} 𝗩𝗲𝗿𝘀𝗶𝗼𝗻: {VERSION}</b>",
        parse_mode="HTML"
    )

# ═══════════════════════════════════════════════════════════════
# 7. /export - تصدير البطاقات الناجحة
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['export'])
def export_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    if user_id not in successful_cards or not successful_cards[user_id]:
        bot.reply_to(message, f"<b>{em('error')} 𝗡𝗼 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹 𝗰𝗮𝗿𝗱𝘀 𝘆𝗲𝘁.</b>", parse_mode="HTML")
        return
    
    filename = f"hits_{user_id}_{int(time.time())}.txt"
    with open(filename, 'w') as f:
        f.write(f"Profesor Checker v{VERSION} - Exported Hits\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        for card in successful_cards[user_id]:
            f.write(f"{card}\n")
    
    with open(filename, 'rb') as f:
        bot.send_document(message.chat.id, f, caption=f"<b>{em('export')} 𝗘𝗫𝗣𝗢𝗥𝗧𝗘𝗗 𝗛𝗜𝗧𝗦\n\n{em('charged')} 𝗧𝗼𝘁𝗮𝗹: {len(successful_cards[user_id])}</b>", parse_mode="HTML")
    
    try:
        os.remove(filename)
    except:
        pass

# ═══════════════════════════════════════════════════════════════
# 8. /bin - معلومات BIN مفصلة
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['bin'])
def bin_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"<b>{em('error')} 𝗨𝘀𝗮𝗴𝗲: <code>/bin 400271</code></b>", parse_mode="HTML")
        return
    
    bin_num = parts[1][:6]
    
    msg = bot.reply_to(message, f"<b>{em('bin')} 𝗟𝗼𝗮𝗱𝗶𝗻𝗴 𝗕𝗜𝗡 𝗶𝗻𝗳𝗼...</b>", parse_mode="HTML")
    
    try:
        r = requests.get(f"https://bins.antipublic.cc/bins/{bin_num}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            text = f"""<b>{em('bin')} 𝗕𝗜𝗡 𝗟𝗢𝗢𝗞𝗨𝗣

🔢 𝗕𝗜𝗡: <code>{bin_num}</code>
💳 𝗕𝗿𝗮𝗻𝗱: {data.get('brand', '-')}
📊 𝗧𝘆𝗽𝗲: {data.get('type', '-')}
⭐ 𝗟𝗲𝘃𝗲𝗹: {data.get('level', '-')}
🏦 𝗕𝗮𝗻𝗸: {data.get('bank', '-')}
🌍 𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {data.get('country_name', '-')} {data.get('country_flag', '')}

{em('code')} 𝗨𝘀𝗮𝗴𝗲: <code>/bin {bin_num}</code></b>"""
        else:
            text = f"<b>{em('error')} 𝗕𝗜𝗡 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱.</b>"
    except Exception as e:
        text = f"<b>{em('error')} 𝗘𝗿𝗿𝗼𝗿: {str(e)[:50]}</b>"
    
    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 9. /fake - توليد بيانات وهمية كاملة
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['fake'])
def fake_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
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
    
    text = f"""<b>{em('fake')} 𝗙𝗔𝗞𝗘 𝗗𝗔𝗧𝗔 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗢𝗥

{em('identity')} 𝗡𝗮𝗺𝗲: <code>{name}</code>
💼 𝗝𝗼𝗯: <code>{job}</code>
🏢 𝗖𝗼𝗺𝗽𝗮𝗻𝘆: <code>{company}</code>
📧 𝗘𝗺𝗮𝗶𝗹: <code>{email}</code>
📱 𝗣𝗵𝗼𝗻𝗲: <code>{phone}</code>
🏠 𝗔𝗱𝗱𝗿𝗲𝘀𝘀:
<code>{address}</code>

💳 𝗖𝗿𝗲𝗱𝗶𝘁 𝗖𝗮𝗿𝗱:
<code>{cc}</code>

{em('code')} 𝗨𝘀𝗮𝗴𝗲: <code>/fake US</code> or <code>/fake GB</code></b>"""
    
    bot.reply_to(message, text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# 10. /check - فحص على كل البوابات
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['check'])
def check_all_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    if not is_code_valid(get_user_code(user_id)) and str(user_id) != str(ADMIN_ID):
        bot.reply_to(message, f"<b>{em('error')} 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗼𝗻𝗹𝘆.</b>", parse_mode="HTML")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"<b>{em('error')} 𝗨𝘀𝗮𝗴𝗲: <code>/check 4405103045656027|10|2026|604</code></b>", parse_mode="HTML")
        return
    
    cc = reg(parts[1])
    if not cc:
        bot.reply_to(message, f"<b>{em('error')} 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗰𝗮𝗿𝗱 𝗳𝗼𝗿𝗺𝗮𝘁.</b>", parse_mode="HTML")
        return
    
    msg = bot.reply_to(message, f"<b>{em('check')} 𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗴 𝗮𝗹𝗹 𝗴𝗮𝘁𝗲𝘄𝗮𝘆𝘀...</b>", parse_mode="HTML")
    
    gateways = [
        ("Stripe Auth", xst_stripe_ezy, "stripe"),
        ("Payments.AI", xst_payments_ai, "paymentsai"),
        ("Braintree", xst_bt_dna, "braintree"),
        ("PayPal 7$", xst_paypal_brass, "paypal")
    ]
    
    results_text = f"<b>{em('check')} 𝗔𝗟𝗟 𝗚𝗔𝗧𝗘𝗪𝗔𝗬𝗦 𝗖𝗛𝗘𝗖𝗞\n\n💳 𝗖𝗮𝗿𝗱: <code>{cc}</code>\n\n"
    
    for name, func, emoji_key in gateways:
        try:
            start = time.time()
            result = func(cc)
            elapsed = time.time() - start
            
            status = "✅" if "APPROVED" in result or "CHARGE" in result else "⚠️" if "CCN" in result else "❌"
            results_text += f"{em(emoji_key)} {name}: {status}\n⏱️ {elapsed:.1f}s | {result[:40]}\n\n"
            
            if "APPROVED" in result or "CHARGE" in result:
                if user_id not in successful_cards:
                    successful_cards[user_id] = []
                successful_cards[user_id].append(f"{cc} | {name}")
        except Exception as e:
            results_text += f"{em(emoji_key)} {name}: ❌\n𝗘𝗿𝗿𝗼𝗿: {str(e)[:30]}\n\n"
    
    results_text += f"{em('skull')} 𝗕𝘆: {BOT_NAME}</b>"
    
    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=results_text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# START + القائمة الرئيسية مع الصورة
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗯𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    if user_id != str(ADMIN_ID) and not is_code_valid(get_user_code(user_id)) and user_id not in pending_activation:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("〔 𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗔𝗰𝘁𝗶𝘃𝗮𝘁𝗶𝗼𝗻 〕", callback_data="request_activation", icon_custom_emoji_id=eid('admin_icon'), style="danger"))
        
        text = f"""<b>{em('welcome')} 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 {BOT_NAME}

{em('declined')} 𝗔𝗖𝗖𝗘𝗦𝗦 𝗗𝗘𝗡𝗜𝗘𝗗
{em('error')} 𝗬𝗼𝘂 𝗻𝗲𝗲𝗱 𝗮𝗻 𝗮𝗰𝘁𝗶𝘃𝗮𝘁𝗶𝗼𝗻 𝗰𝗼𝗱𝗲.

{em('choose')} 𝗖𝗹𝗶𝗰𝗸 𝗯𝗲𝗹𝗼𝘄 𝘁𝗼 𝗿𝗲𝗾𝘂𝗲𝘀𝘁 𝗮𝗰𝗰𝗲𝘀𝘀</b>"""
        
        bot.send_photo(message.chat.id, BANNER_URL, caption=text, reply_markup=markup, parse_mode="HTML")
        return
    
    name = message.from_user.first_name
    if user_id not in user_stats:
        user_stats[user_id] = {'total': 0, 'charged': 0, 'funds': 0, 'ccn': 0, 'declined': 0}
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("〔 𝗧𝗼𝗼𝗹𝘀 〕", callback_data="menu_tools", icon_custom_emoji_id=eid('tools'), style="primary"),
        InlineKeyboardButton("〔 𝗣𝗿𝗼𝘅𝘆 〕", callback_data="menu_proxy", icon_custom_emoji_id=eid('proxy'), style="success")
    )
    markup.add(
        InlineKeyboardButton("〔 𝗡𝗲𝘄 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀 〕", callback_data="menu_new", icon_custom_emoji_id=eid('code'), style="primary"),
        InlineKeyboardButton("〔 𝗗𝗲𝘃 〕", callback_data="menu_dev", icon_custom_emoji_id=eid('developer'), style="danger")
    )
    markup.add(InlineKeyboardButton("〔 𝗣𝗿𝗼𝗳𝗶𝗹𝗲 〕", callback_data="menu_profile", icon_custom_emoji_id=eid('profile_icon'), style="primary"))
    
    text = f"""<b>✦ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 {name} 𝐓𝐎 {BOT_NAME} ✦

【{em('gateway')}】 𝗚𝗔𝗧𝗘𝗪𝗔𝗬𝗦 ➛ 𝙎𝙩𝙧𝙞𝙥𝙚 + 𝘽𝙧𝙖𝙞𝙣𝙩𝙧𝙚𝙚 + 𝐏𝐚𝐲𝐏𝐚𝐥 + 𝐏𝐚𝐲𝐦𝐞𝐧𝐭𝐬.𝐀𝐈
【{em('mode')}】 𝗠𝗢𝗗𝗘 ➛ 𝘼𝙪𝙩𝙝 + 𝘾𝙝𝙖𝙧𝙜𝙚
【{em('speed')}】 𝗦𝗣𝗘𝗘𝗗 ➛ 𝙐𝙡𝙩𝙧𝙖 𝙁𝙖𝙨𝙩
【{em('status_icon')}】 𝗦𝗧𝗔𝗧𝗨𝗦 ➛ 𝙎𝙩𝙖𝙗𝙡𝙚 + 𝙎𝙚𝙘𝙪𝙧𝙚
【{em('version_icon')}】 𝗩𝗘𝗥𝗦𝗜𝗢𝗡 ➛ {VERSION}

━━━━━━━━━━━━━━━━━━━━━━━━

【「{em('choose')}」】 𝗖𝗛𝗢𝗢𝗦𝗘 𝗔 𝗦𝗘𝗥𝗩𝗜𝗖𝗘 【「{em('choose')}」】</b>"""
    
    bot.send_photo(message.chat.id, BANNER_URL, caption=text, reply_markup=markup, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# قائمة الأوامر الجديدة
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data == 'menu_new')
def menu_new(call):
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("〔 𝗜𝗕𝗔𝗡 〕", callback_data="cmd_iban", icon_custom_emoji_id=eid('iban'), style="primary"),
        InlineKeyboardButton("〔 𝗜𝗱𝗲𝗻𝘁𝗶𝘁𝘆 〕", callback_data="cmd_identity", icon_custom_emoji_id=eid('identity'), style="success")
    )
    markup.add(
        InlineKeyboardButton("〔 𝗣𝗿𝗼𝘅𝘆 𝗖𝗵𝗸 〕", callback_data="cmd_proxy", icon_custom_emoji_id=eid('proxy'), style="primary"),
        InlineKeyboardButton("〔 𝗠𝗮𝘀𝘀 〕", callback_data="cmd_mass", icon_custom_emoji_id=eid('mass'), style="danger")
    )
    markup.add(
        InlineKeyboardButton("〔 𝗦𝘁𝗮𝘁𝘀 〕", callback_data="cmd_stats", icon_custom_emoji_id=eid('stats'), style="primary"),
        InlineKeyboardButton("〔 𝗣𝗶𝗻𝗴 〕", callback_data="cmd_ping", icon_custom_emoji_id=eid('ping'), style="success")
    )
    markup.add(
        InlineKeyboardButton("〔 𝗘𝘅𝗽𝗼𝗿𝘁 〕", callback_data="cmd_export", icon_custom_emoji_id=eid('export'), style="primary"),
        InlineKeyboardButton("〔 𝗕𝗜𝗡 〕", callback_data="cmd_bin", icon_custom_emoji_id=eid('bin'), style="success")
    )
    markup.add(
        InlineKeyboardButton("〔 𝗙𝗮𝗸𝗲 〕", callback_data="cmd_fake", icon_custom_emoji_id=eid('fake'), style="primary"),
        InlineKeyboardButton("〔 𝗖𝗵𝗲𝗰𝗸 𝗔𝗹𝗹 〕", callback_data="cmd_check", icon_custom_emoji_id=eid('check'), style="danger")
    )
    markup.add(InlineKeyboardButton("〔 🔙 𝗕𝗮𝗰𝗸 〕", callback_data="menu_back", icon_custom_emoji_id=eid('back_icon'), style="danger"))
    
    text = f"""<b>{em('tools')} 𝗡𝗘𝗪 𝗖𝗢𝗠𝗠𝗔𝗡𝗗𝗦 𝗠𝗘𝗡𝗨
━━━━━━━━━━━━━━━━━━━━━━━━

{em('iban')} /iban - Generate fake IBAN
{em('identity')} /identity - Generate full identity
{em('proxy')} /proxy - Check proxy status
{em('mass')} /mass - Mass card check
{em('stats')} /stats - Your statistics
{em('ping')} /ping - Bot speed test
{em('export')} /export - Export hits
{em('bin')} /bin - BIN lookup
{em('fake')} /fake - Generate fake data
{em('check')} /check - Check all gateways

{em('choose')} Select a command</b>"""
    
    bot.edit_message_media(
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(BANNER_URL, caption=text, parse_mode='HTML'),
        reply_markup=markup
    )

# Callback handlers للأوامر الجديدة
@bot.callback_query_handler(func=lambda call: call.data.startswith('cmd_'))
def cmd_callbacks(call):
    bot.answer_callback_query(call.id)
    cmd = call.data.replace('cmd_', '')
    
    examples = {
        'iban': '/iban DE\n/iban GB\n/iban FR',
        'identity': '/identity US\n/identity GB\n/identity DE',
        'proxy': '/proxy 1.2.3.4:8080\n/proxy 1.2.3.4:8080:user:pass',
        'mass': '/mass\n4405...|10|2026|604\n4405...|11|2027|605',
        'stats': '/stats',
        'ping': '/ping',
        'export': '/export',
        'bin': '/bin 400271\n/bin 515676',
        'fake': '/fake US\n/fake GB\n/fake DE',
        'check': '/check 4405103045656027|10|2026|604'
    }
    
    text = f"<b>{em(cmd)} 𝗖𝗢𝗠𝗠𝗔𝗡𝗗: /{cmd}\n\n{em('code')} 𝗨𝘀𝗮𝗴𝗲:\n<code>{examples.get(cmd, '/' + cmd)}</code>\n\n{em('choose')} Send the command in chat</b>"
    
    bot.send_message(call.message.chat.id, text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# الأوامر القديمة (موجودة سابقاً)
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data == 'menu_tools')
def menu_tools(call):
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("〔 𝐒𝐭𝐫𝐢𝐩𝐞 〕", callback_data="check_stripe_ezy", icon_custom_emoji_id=eid('stripe'), style="primary"),
        InlineKeyboardButton("〔 𝐏𝐚𝐲𝐦𝐞𝐧𝐭𝐬.𝐀𝐈 〕", callback_data="check_payments_ai", icon_custom_emoji_id=eid('paymentsai'), style="danger")
    )
    markup.add(
        InlineKeyboardButton("〔 𝘽𝙧𝙖𝙞𝙣𝙩𝙧𝙚𝙚 〕", callback_data="check_braintree", icon_custom_emoji_id=eid('braintree'), style="success"),
        InlineKeyboardButton("〔 𝐏𝐚𝐲𝐏𝐚𝐥 𝟳$ 〕", callback_data="check_paypal", icon_custom_emoji_id=eid('paypal'), style="primary")
    )
    markup.add(InlineKeyboardButton("〔 𝗖𝗼𝗺𝗯𝗼 𝗖𝗵𝗲𝗰𝗸 〕", callback_data="check_combo", icon_custom_emoji_id=eid('combo_card'), style="success"))
    markup.add(InlineKeyboardButton("〔 🔙 𝗕𝗮𝗰𝗸 〕", callback_data="menu_back", icon_custom_emoji_id=eid('back_icon'), style="danger"))
    
    text = f"<b>{em('tools')} 𝗧𝗢𝗢𝗟𝗦 𝗠𝗘𝗡𝗨\n━━━━━━━━━━━━━━━━━━━━━━━━\n{em('choose')} 𝗦𝗲𝗹𝗲𝗰𝘁 𝗮 𝗴𝗮𝘁𝗲𝘄𝗮𝘆 𝘁𝗼 𝗰𝗵𝗲𝗰𝗸 𝗰𝗮𝗿𝗱</b>"
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'menu_back')
def menu_back(call):
    bot.answer_callback_query(call.id)
    name = call.from_user.first_name
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("〔 𝗧𝗼𝗼𝗹𝘀 〕", callback_data="menu_tools", icon_custom_emoji_id=eid('tools'), style="primary"),
        InlineKeyboardButton("〔 𝗣𝗿𝗼𝘅𝘆 〕", callback_data="menu_proxy", icon_custom_emoji_id=eid('proxy'), style="success")
    )
    markup.add(
        InlineKeyboardButton("〔 𝗡𝗲𝘄 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀 〕", callback_data="menu_new", icon_custom_emoji_id=eid('code'), style="primary"),
        InlineKeyboardButton("〔 𝗗𝗲𝘃 〕", callback_data="menu_dev", icon_custom_emoji_id=eid('developer'), style="danger")
    )
    markup.add(InlineKeyboardButton("〔 𝗣𝗿𝗼𝗳𝗶𝗹𝗲 〕", callback_data="menu_profile", icon_custom_emoji_id=eid('profile_icon'), style="primary"))
    
    text = f"""<b>✦ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 {name} 𝐓𝐎 {BOT_NAME} ✦

【{em('gateway')}】 𝗚𝗔𝗧𝗘𝗪𝗔𝗬𝗦 ➛ 𝙎𝙩𝙧𝙞𝙥𝙚 + 𝘽𝙧𝙖𝙞𝙣𝙩𝙧𝙚𝙚 + 𝐏𝐚𝐲𝐏𝐚𝐥 + 𝐏𝐚𝐲𝐦𝐞𝐧𝐭𝐬.𝐀𝐈
【{em('mode')}】 𝗠𝗢𝗗𝗘 ➛ 𝘼𝙪𝙩𝙝 + 𝘾𝙝𝙖𝙧𝙜𝙚
【{em('speed')}】 𝗦𝗣𝗘𝗘𝗗 ➛ 𝙐𝙡𝙩𝙧𝙖 𝙁𝙖𝙨𝙩
【{em('status_icon')}】 𝗦𝗧𝗔𝗧𝗨𝗦 ➛ 𝙎𝙩𝙖𝙗𝙡𝙚 + 𝙎𝙚𝙘𝙪𝙧𝙚

━━━━━━━━━━━━━━━━━━━━━━━━

【「{em('choose')}」】 𝗖𝗛𝗢𝗢𝗦𝗘 𝗔 𝗦𝗘𝗥𝗩𝗜𝗖𝗘 【「{em('choose')}」】</b>"""
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=markup, parse_mode="HTML")

# ... (بقية الأوامر القديمة تبقى كما هي من الملف السابق)

print(f'✦ {BOT_NAME} {VERSION} 𝗥𝘂𝗻𝗻𝗶𝗻𝗴...')
print(f'💎 𝗗𝗲𝘃: {DEVELOPER_USERNAME}')
print(f'🚀 𝗚𝗮𝘁𝗲𝘄𝗮𝘆𝘀: Stripe + Payments.AI + Braintree + PayPal')
print(f'🔥 𝗡𝗲𝘄 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀: /iban /identity /proxy /mass /stats /ping /export /bin /fake /check')

while True:
    try: bot.infinity_polling()
    except Exception as e: print(f'❌ 𝗘𝗿𝗿𝗼𝗿: {e}'); time.sleep(5)
