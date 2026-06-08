''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Mo.dark جاهز 🕷️☠️
# Profesor Checker v11.0 ULTIMATE

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
    if user_id not in user_stats: return f"<b>{em('error')} 𝗡𝗼 𝘀𝘁𝗮𝘁𝘀 𝘆𝗲𝘁</b>"
    s = user_stats[user_id]
    return f"""<b>{em('stats')} 𝗬𝗢𝗨𝗥 𝗦𝗧𝗔𝗧𝗦
{em('charged')} 𝗖𝗵𝗮𝗿𝗴𝗲𝗱: {s['charged']}
{em('funds')} 𝗙𝘂𝗻𝗱𝘀: {s['funds']}
{em('ccn')} 𝗖𝗖𝗡: {s['ccn']}
{em('declined')} 𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱: {s['declined']}
{em('gateway')} 𝗧𝗼𝘁𝗮𝗹: {s['total']}</b>"""

def get_user_status(user_id):
    if str(user_id) == str(ADMIN_ID): return f"{em('crown')} 𝗔𝗗𝗠𝗜𝗡"
    if is_user_premium(user_id):
        code = get_user_code(user_id)
        if code:
            expiry = user_codes.get(code, {}).get('expiry')
            if expiry:
                days_left = (expiry - datetime.now()).days
                return f"{em('star')} 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 ({days_left} days)"
        return f"{em('star')} 𝗣𝗥𝗘𝗠𝗜𝗨𝗠"
    return f"{em('lock')} 𝗙𝗥𝗘𝗘"

# ═══════════════════════════════════════════════════════════════
# تنسيق مخرجات البطاقة
# ═══════════════════════════════════════════════════════════════

def format_card_result(cc, gateway_name, gateway_cmd, result, elapsed, bin_info=""):
    """تنسيق مخرجات البطاقة بالشكل المطلوب"""
    status = "APPROVED" if "APPROVED" in result or "CHARGE" in result else "CCN" if "CCN" in result else "DECLINED"
    status_emoji = "✅" if status == "APPROVED" else "⚠️" if status == "CCN" else "❌"
    
    text = f"""<b>[ϟ] 𝗚𝗮𝘁𝗲𝘄𝗮𝘆: {gateway_name} [ {gateway_cmd} ]
-------------------------------
[ϟ] 𝗖𝗮𝗿𝗱: <code>{cc}</code> {GATEWAYS.get(gateway_cmd.replace('/',''), {}).get('color', '🔥')}
[ϟ] 𝗦𝘁𝗮𝘁𝘂𝘀: {status}! {status_emoji}
[ϟ] 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: {result}
-------------------------------
{bin_info}
-------------------------------
[ϟ] 𝗧𝗶𝗺𝗲: {elapsed:.2f}s ⏱
[ϟ] 𝗣𝗿𝗶𝗰𝗲: {GATEWAYS.get(gateway_cmd.replace('/',''), {}).get('price', '$0.00')}
[ϟ] 𝗕𝘆: {BOT_NAME}
-------------------------------
[ϟ] 𝗗𝗲𝘃: {DEVELOPER_USERNAME} - 💀</b>"""
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
# 4. /mass - فحص مجموعة بطاقات (نظام الكومبو المتقدم)
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['mass'])
def mass_check_command(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    if not is_user_premium(user_id):
        bot.reply_to(message, f"<b>{em('error')} 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗼𝗻𝗹𝘆.\n\n{em('star')} استخدم /stars للاشتراك بالنجوم</b>", parse_mode="HTML")
        return
    
    parts = message.text.split('\n', 1)
    if len(parts) < 2:
        text = f"""<<b>{em('error')} 𝗨𝘀𝗮𝗴𝗲:
<code>/mass
4405...|10|2026|604
4405...|11|2027|605</code></b>"""
        bot.reply_to(message, text, parse_mode="HTML")

        return
    
    cards_text = parts[1]
    cards = extract_cc(cards_text)
    
    if not cards:
        bot.reply_to(message, f"<b>{em('error')} 𝗡𝗼 𝘃𝗮𝗹𝗶𝗱 𝗰𝗮𝗿𝗱𝘀 𝗳𝗼𝘂𝗻𝗱.</b>", parse_mode="HTML")
        return
    
    max_cards = MASS_CONFIG['premium_max_cards'] if is_user_premium(user_id) else MASS_CONFIG['free_max_cards']
    if len(cards) > max_cards:
        bot.reply_to(message, f"<b>{em('error')} 𝗠𝗮𝘅 {max_cards} 𝗰𝗮𝗿𝗱𝘀. 𝗬𝗼𝘂 𝘀𝗲𝗻𝘁 {len(cards)}.</b>", parse_mode="HTML")
        return
    
    # إنشاء رسالة الكومبو
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🟢 Approved 0", callback_data="mass_approved"))
    markup.add(InlineKeyboardButton("🔵 3D Secure 0", callback_data="mass_3d"))
    markup.add(InlineKeyboardButton("🔴 Declined 0", callback_data="mass_declined"))
    markup.add(InlineKeyboardButton("⏹ Stop", callback_data="mass_stop"))
    
    msg = bot.send_message(
        message.chat.id,
        f"""<b>{em('mass')} 𝗠𝗔𝗦𝗦 𝗖𝗛𝗘𝗖𝗞

📁 {em('folder')} Stripe Auth Mass Check
{em('plan_icon')} Your Plan: {'⭐ Premium' if is_user_premium(user_id) else '🆓 Free'}
{em('limit')} Max Cards: {max_cards}
{em('file')} Send me a `.txt` file

{em('card')} Format: 4111111111111111|12|2028|123
{em('checkmark')} One card per line

⏳ Checking {len(cards)} cards...</b>""",
        reply_markup=markup,
        parse_mode="HTML"
    )
    
    # بدء الفحص
    results = {'approved': [], 'ccn': [], 'declined': [], 'total': len(cards)}
    session_id = f"{user_id}_{int(time.time())}"
    mass_sessions[session_id] = {'active': True, 'msg_id': msg.message_id, 'chat_id': message.chat.id}
    
    for i, card in enumerate(cards):
        if not mass_sessions.get(session_id, {}).get('active', False):
            break
        
        try:
            result = xst_stripe_ezy(card)
            
            if "APPROVED" in result:
                results['approved'].append(card)
            elif "CCN" in result:
                results['ccn'].append(card)
            else:
                results['declined'].append(card)
            
            # تحديث كل 5 بطاقات
            if (i + 1) % MASS_CONFIG['show_progress_every'] == 0 or i == len(cards) - 1:
                markup = InlineKeyboardMarkup(row_width=1)
                markup.add(InlineKeyboardButton(f"🟢 Approved {len(results['approved'])}", callback_data="mass_approved"))
                markup.add(InlineKeyboardButton(f"🔵 3D Secure {len(results['ccn'])}", callback_data="mass_3d"))
                markup.add(InlineKeyboardButton(f"🔴 Declined {len(results['declined'])}", callback_data="mass_declined"))
                markup.add(InlineKeyboardButton("⏹ Stop", callback_data=f"mass_stop_{session_id}"))
                
                try:
                    bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        text=f"""<b>{em('mass')} 𝗠𝗔𝗦𝗦 𝗖𝗛𝗘𝗖𝗞 𝗣𝗥𝗢𝗚𝗥𝗘𝗦𝗦

📁 {em('folder')} Stripe Auth Mass Check
{em('plan_icon')} Your Plan: {'⭐ Premium' if is_user_premium(user_id) else '🆓 Free'}
{em('limit')} Max Cards: {max_cards}
{em('card')} Format: 4111111111111111|12|2028|123
{em('checkmark')} One card per line

✅ Will check first {len(cards)} cards

{em('card')} Card: {card}
{em('response_icon')} Response: {result[:40]}...

🟢 Approved: {len(results['approved'])}
🔵 3D Secure: {len(results['ccn'])}
🔴 Declined: {len(results['declined'])}
📊 Total: {i+1}/{len(cards)}</b>""",
                        reply_markup=markup,
                        parse_mode="HTML"
                    )
                except:
                    pass
            
            time.sleep(MASS_CONFIG['delay_between_cards'])
        except Exception as e:
            results['declined'].append(card)
    
    # النتيجة النهائية
    mass_sessions[session_id]['active'] = False
    
    # حفظ البطاقات الناجحة
    if user_id not in successful_cards:
        successful_cards[user_id] = []
    successful_cards[user_id].extend(results['approved'])
    successful_cards[user_id].extend(results['ccn'])
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(f"🟢 Approved {len(results['approved'])}", callback_data="mass_approved"))
    markup.add(InlineKeyboardButton(f"🔵 3D Secure {len(results['ccn'])}", callback_data="mass_3d"))
    markup.add(InlineKeyboardButton(f"🔴 Declined {len(results['declined'])}", callback_data="mass_declined"))
    
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=msg.message_id,
        text=f"""<b>{em('mass')} 𝗠𝗔𝗦𝗦 𝗖𝗛𝗘𝗖𝗞 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘

📁 {em('folder')} Stripe Auth Mass Check
{em('plan_icon')} Your Plan: {'⭐ Premium' if is_user_premium(user_id) else '🆓 Free'}
{em('limit')} Max Cards: {max_cards}

🟢 Approved: {len(results['approved'])}
🔵 3D Secure: {len(results['ccn'])}
🔴 Declined: {len(results['declined'])}
📊 Total: {len(cards)}

{em('skull')} 𝗕𝘆: {BOT_NAME}</b>""",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('mass_stop_'))
def mass_stop_callback(call):
    bot.answer_callback_query(call.id)
    session_id = call.data.replace('mass_stop_', '')
    if session_id in mass_sessions:
        mass_sessions[session_id]['active'] = False
    bot.send_message(call.message.chat.id, f"<b>{em('stop')} 𝗠𝗮𝘀𝘀 𝗰𝗵𝗲𝗰𝗸 𝘀𝘁𝗼𝗽𝗽𝗲𝗱.</b>", parse_mode="HTML")

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
    
    if not is_user_premium(user_id):
        bot.reply_to(message, f"<b>{em('error')} 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗼𝗻𝗹𝘆.\n\n{em('star')} استخدم /stars للاشتراك بالنجوم</b>", parse_mode="HTML")
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
        ("Stripe 0.00$", xst_stripe_ezy, "stripe", "/st"),
        ("Payments.AI", xst_payments_ai, "paymentsai", "/pa"),
        ("Braintree", xst_bt_dna, "braintree", "/bt"),
        ("PayPal 7$", xst_paypal_brass, "paypal", "/pp")
    ]
    
    results_text = f"<b>{em('check')} 𝗔𝗟𝗟 𝗚𝗔𝗧𝗘𝗪𝗔𝗬𝗦 𝗖𝗛𝗘𝗖𝗞\n\n💳 𝗖𝗮𝗿𝗱: <code>{cc}</code>\n\n"
    
    for name, func, emoji_key, cmd in gateways:
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

# ═══════════════════════════════════════════════════════════
# bot.py v11.0 - الجزء 2/4
# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
# نظام الدفع بالنجوم (Telegram Stars) - حقيقي
# ═══════════════════════════════════════════════════════════

@bot.message_handler(commands=['stars'])
def stars_menu(message):
    """عرض قائمة الاشتراكات بالنجوم"""
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for key, plan in STARS_PRICES.items():
        markup.add(InlineKeyboardButton(
            f"〔 {plan['label']} - {plan['price']} ⭐ 〕",
            callback_data=f"stars_buy_{key}"
        ))
    
    markup.add(InlineKeyboardButton(
        "〔 🔙 𝗥𝗲𝘁𝘂𝗿𝗻 〕",
        callback_data="menu_back"
    ))
    
    text = f"""<b>{em('star')} 𝗦𝗧𝗔𝗥𝗦 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗦𝗬𝗦𝗧𝗘𝗠

{em('crown')} اختر باقة الاشتراك:

{em('star')} يوم واحد - 1 ⭐
{em('star')} أسبوع - 5 ⭐
{em('star')} شهر - 15 ⭐
{em('star')} 3 أشهر - 40 ⭐
{em('star')} 6 أشهر - 70 ⭐
{em('star')} سنة - 120 ⭐

{em('choose')} اضغط على الباقة المطلوبة</b>"""
    
    bot.send_photo(message.chat.id, BANNER_URL, caption=text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('stars_buy_'))
def stars_buy_callback(call):
    """معالجة طلب شراء بالنجوم"""
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    plan_key = call.data.replace('stars_buy_', '')
    
    if plan_key not in STARS_PRICES:
        bot.send_message(call.message.chat.id, f"<b>{em('error')} خطة غير صالحة</b>", parse_mode="HTML")
        return
    
    plan = STARS_PRICES[plan_key]
    
    prices = [LabeledPrice(label=f"اشتراك {plan['label']}", amount=plan['price'])]
    
    bot.send_invoice(
        chat_id=call.message.chat.id,
        title=f"Profesor Checker - {plan['label']}",
        description=f"اشتراك بـ {plan['price']} نجمة ⭐ لمدة {plan['label']}",
        invoice_payload=f"stars_{plan_key}_{user_id}_{int(time.time())}",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter=f"stars_{plan_key}",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                f"〔 ادفع {plan['price']} ⭐ 〕",
                pay=True
            )
        )
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def stars_pre_checkout(query):
    """التحقق من الفاتورة قبل الدفع"""
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def stars_successful_payment(message):
    """معالجة الدفع الناجح بالنجوم"""
    user_id = str(message.from_user.id)
    payload = message.successful_payment.invoice_payload
    
    try:
        parts = payload.split('_')
        plan_key = parts[1]
        plan = STARS_PRICES[plan_key]
        
        expiry = datetime.now() + timedelta(days=plan['days'])
        code = f"STARS-{user_id}-{int(time.time())}"
        
        user_codes[code] = {
            'user_id': user_id,
            'expiry': expiry,
            'type': 'stars',
            'plan': plan_key,
            'price': plan['price']
        }
        
        text = f"""<b>{em('success')} 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟!

{em('star')} تم الدفع بنجاح!
{em('time')} مدة الاشتراك: {plan['label']}
{em('calendar')} ينتهي في: {expiry.strftime('%Y-%m-%d %H:%M')}
{em('unlock')} الحالة: 𝗣𝗥𝗘𝗠𝗜𝗨𝗠

{em('fire')} يمكنك الآن استخدام جميع الميزات!</b>"""
        
        bot.send_message(message.chat.id, text, parse_mode="HTML")
        
        try:
            admin_text = f"""<b>{em('star')} 𝗡𝗘𝗪 𝗦𝗧𝗔𝗥𝗦 𝗣𝗔𝗬𝗠𝗘𝗡𝗧

👤 User ID: <code>{user_id}</code>
📦 Plan: {plan['label']}
⭐ Stars: {plan['price']}
📅 Expiry: {expiry.strftime('%Y-%m-%d')}

{em('money')} النجوم تم تحويلها لحسابك تلقائياً!</b>"""
            bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
        except:
            pass
            
    except Exception as e:
        bot.send_message(message.chat.id, f"<b>{em('error')} خطأ في معالجة الدفع: {str(e)[:50]}</b>", parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# START + القائمة الرئيسية
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗯𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    if user_id != str(ADMIN_ID) and not is_user_premium(user_id) and user_id not in pending_activation:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton(
            "〔 𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗔𝗰𝘁𝗶𝘃𝗮𝘁𝗶𝗼𝗻 〕",
            callback_data="request_activation"
        ))
        markup.add(InlineKeyboardButton(
            "〔 ⭐ اشترك بالنجوم 〕",
            callback_data="stars_menu"
        ))
        
        text = f"""<b>{em('welcome')} 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 {BOT_NAME}

{em('declined')} 𝗔𝗖𝗖𝗘𝗦𝗦 𝗗𝗘𝗡𝗜𝗘𝗗
{em('error')} 𝗬𝗼𝘂 𝗻𝗲𝗲𝗱 𝗮𝗻 𝗮𝗰𝘁𝗶𝘃𝗮𝘁𝗶𝗼𝗻 𝗰𝗼𝗱𝗲.

{em('choose')} اختر طريقة التفعيل:</b>"""
        
        bot.send_photo(message.chat.id, BANNER_URL, caption=text, reply_markup=markup, parse_mode="HTML")
        return
    
    name = message.from_user.first_name
    if user_id not in user_stats:
        user_stats[user_id] = {'total': 0, 'charged': 0, 'funds': 0, 'ccn': 0, 'declined': 0}
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("〔 𝗧𝗼𝗼𝗹𝘀 〕", callback_data="menu_tools"),
        InlineKeyboardButton("〔 𝗣𝗿𝗼𝘅𝘆 〕", callback_data="menu_proxy")
    )
    markup.add(
        InlineKeyboardButton("〔 𝗡𝗲𝘄 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀 〕", callback_data="menu_new"),
        InlineKeyboardButton("〔 𝗗𝗲𝘃 〕", callback_data="menu_dev")
    )
    markup.add(
        InlineKeyboardButton("〔 ⭐ اشترك بالنجوم 〕", callback_data="stars_menu"),
        InlineKeyboardButton("〔 𝗣𝗿𝗼𝗳𝗶𝗹𝗲 〕", callback_data="menu_profile")
    )
    
    status = get_user_status(user_id)
    
    text = f"""<b>✦ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 {name} 𝐓𝐎 {BOT_NAME} ✦

【{em('gateway')}】 𝗚𝗔𝗧𝗘𝗪𝗔𝗬𝗦 ➛ 𝙎𝙩𝙧𝙞𝙥𝙚 + 𝘽𝙧𝙖𝙞𝙣𝙩𝙧𝙚𝙚 + 𝐏𝐚𝐲𝐏𝐚𝐥 + 𝐏𝐚𝐲𝐦𝐞𝐧𝐭𝐬.𝐀𝐈
【{em('mode')}】 𝗠𝗢𝗗𝗘 ➛ 𝘼𝙪𝙩𝙝 + 𝘾𝙝𝙖𝙧𝙜𝙚
【{em('speed')}】 𝗦𝗣𝗘𝗘𝗗 ➛ 𝙐𝙡𝙩𝙧𝙖 𝙁𝙖𝙨𝙩
【{em('status_icon')}】 𝗦𝗧𝗔𝗧𝗨𝗦 ➛ {status}
【{em('version_icon')}】 𝗩𝗘𝗥𝗦𝗜𝗢𝗡 ➛ {VERSION}

━━━━━━━━━━━━━━━━━━━━━━━━

【「{em('choose')}」】 𝗖𝗛𝗢𝗢𝗦𝗘 𝗔 𝗦𝗘𝗥𝗩𝗜𝗖𝗘 【「{em('choose')}」】</b>"""
    
    bot.send_photo(message.chat.id, BANNER_URL, caption=text, reply_markup=markup, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# bot.py v11.0 - الجزء 3/4

@bot.callback_query_handler(func=lambda call: call.data == 'stars_menu')
def stars_menu_callback(call):
    """عرض قائمة النجوم من الزر"""
    bot.answer_callback_query(call.id)
    stars_menu(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'request_activation')
def request_activation_callback(call):
    """طلب تفعيل من الأدمن"""
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    username = call.from_user.username or "N/A"
    
    if user_id in pending_activation:
        bot.send_message(call.message.chat.id, f"<b>{em('error')} لقد أرسلت طلباً بالفعل، انتظر الرد.</b>", parse_mode="HTML")
        return
    
    pending_activation[user_id] = {'time': datetime.now(), 'username': username}
    
    try:
        admin_text = f"""<b>{em('admin_icon')} 𝗡𝗘𝗪 𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗜𝗢𝗡 𝗥𝗘𝗤𝗨𝗘𝗦𝗧

👤 User ID: <code>{user_id}</code>
📛 Username: @{username}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{em('code')} للموافقة:
<code>/approve {user_id} 7</code> (7 أيام)
<code>/approve {user_id} 30</code> (30 يوم)</b>"""
        
        admin_markup = InlineKeyboardMarkup(row_width=2)
        admin_markup.add(
            InlineKeyboardButton("〔 ✅ موافقة 7 أيام 〕", callback_data=f"approve_{user_id}_7"),
            InlineKeyboardButton("〔 ✅ موافقة 30 يوم 〕", callback_data=f"approve_{user_id}_30")
        )
        admin_markup.add(
            InlineKeyboardButton("〔 ❌ رفض 〕", callback_data=f"reject_{user_id}")
        )
        
        bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_markup, parse_mode="HTML")
    except Exception as e:
        print(f"Error notifying admin: {e}")
    
    bot.send_message(call.message.chat.id, f"<b>{em('success')} تم إرسال طلب التفعيل للأدمن.\n{em('time')} انتظر الرد...\n\n{em('star')} أو اشترك بالنجوم فوراً عبر /stars</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
def approve_callback(call):
    """موافقة الأدمن على طلب"""
    bot.answer_callback_query(call.id)
    
    if str(call.from_user.id) != str(ADMIN_ID):
        bot.send_message(call.message.chat.id, f"<b>{em('error')} غير مصرح!</b>", parse_mode="HTML")
        return
    
    parts = call.data.split('_')
    user_id = parts[1]
    days = int(parts[2]) if len(parts) > 2 else 7
    
    code = generate_code()
    expiry = datetime.now() + timedelta(days=days)
    user_codes[code] = {'user_id': user_id, 'expiry': expiry, 'type': 'admin'}
    
    try:
        user_text = f"""<b>{em('success')} 𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗜𝗢𝗡 𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗!

{em('code')} Your Code: <code>{code}</code>
{em('time')} Valid until: {expiry.strftime('%Y-%m-%d %H:%M')}
{em('unlock')} Status: 𝗣𝗥𝗘𝗠𝗜𝗨𝗠

{em('fire')} Send /start to access!</b>"""
        bot.send_message(user_id, user_text, parse_mode="HTML")
    except:
        pass
    
    bot.edit_message_text(
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        text=f"<b>{em('success')} تم الموافقة على المستخدم {user_id}\n{em('code')} الكود: <code>{code}</code>\n{em('time')} صالح لـ {days} يوم</b>",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def reject_callback(call):
    """رفض طلب الأدمن"""
    bot.answer_callback_query(call.id)
    
    if str(call.from_user.id) != str(ADMIN_ID):
        bot.send_message(call.message.chat.id, f"<b>{em('error')} غير مصرح!</b>", parse_mode="HTML")
        return
    
    user_id = call.data.split('_')[1]
    
    try:
        bot.send_message(user_id, f"<b>{em('declined')} تم رفض طلب التفعيل.\n{em('star')} يمكنك الاشتراك بالنجوم عبر /stars</b>", parse_mode="HTML")
    except:
        pass
    
    bot.edit_message_text(
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        text=f"<b>{em('declined')} تم رفض المستخدم {user_id}</b>",
        parse_mode="HTML"
    )

# ═══════════════════════════════════════════════════════════════
# قائمة الأوامر الجديدة
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data == 'menu_new')
def menu_new(call):
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("〔 𝗜𝗕𝗔𝗡 〕", callback_data="cmd_iban"),
        InlineKeyboardButton("〔 𝗜𝗱𝗲𝗻𝘁𝗶𝘁𝘆 〕", callback_data="cmd_identity")
    )
    markup.add(
        InlineKeyboardButton("〔 𝗣𝗿𝗼𝘅𝘆 𝗖𝗵𝗸 〕", callback_data="cmd_proxy"),
        InlineKeyboardButton("〔 𝗠𝗮𝘀𝘀 〕", callback_data="cmd_mass")
    )
    markup.add(
        InlineKeyboardButton("〔 𝗦𝘁𝗮𝘁𝘀 〕", callback_data="cmd_stats"),
        InlineKeyboardButton("〔 𝗣𝗶𝗻𝗴 〕", callback_data="cmd_ping")
    )
    markup.add(
        InlineKeyboardButton("〔 𝗘𝘅𝗽𝗼𝗿𝘁 〕", callback_data="cmd_export"),
        InlineKeyboardButton("〔 𝗕𝗜𝗡 〕", callback_data="cmd_bin")
    )
    markup.add(
        InlineKeyboardButton("〔 𝗙𝗮𝗸𝗲 〕", callback_data="cmd_fake"),
        InlineKeyboardButton("〔 𝗖𝗵𝗲𝗰𝗸 𝗔𝗹𝗹 〕", callback_data="cmd_check")
    )
    markup.add(InlineKeyboardButton("〔 🔙 𝗕𝗮𝗰𝗸 〕", callback_data="menu_back"))
    
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
        media=InputMediaPhoto(BANNER_URL, caption=text, parse_mode='HTML'),
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
# قائمة الأدوات (الأزرار القديمة - مُصلحة)
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data == 'menu_tools')
def menu_tools(call):
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("〔 𝐒𝐭𝐫𝐢𝐩𝐞 〕", callback_data="check_stripe_ezy"),
        InlineKeyboardButton("〔 𝐏𝐚𝐲𝐦𝐞𝐧𝐭𝐬.𝐀𝐈 〕", callback_data="check_payments_ai")
    )
    markup.add(
        InlineKeyboardButton("〔 𝘽𝙧𝙖𝙞𝙣𝙩𝙧𝙚𝙚 〕", callback_data="check_braintree"),
        InlineKeyboardButton("〔 𝐏𝐚𝐲𝐏𝐚𝐥 𝟳$ 〕", callback_data="check_paypal")
    )
    markup.add(InlineKeyboardButton("〔 🔙 𝗕𝗮𝗰𝗸 〕", callback_data="menu_back"))
    
    text = f"<b>{em('tools')} 𝗧𝗢𝗢𝗟𝗦 𝗠𝗘𝗡𝗨\n━━━━━━━━━━━━━━━━━━━━━━━━\n{em('choose')} 𝗦𝗲𝗹𝗲𝗰𝘁 𝗮 𝗴𝗮𝘁𝗲𝘄𝗮𝘆 𝘁𝗼 𝗰𝗵𝗲𝗰𝗸 𝗰𝗮𝗿𝗱</b>"
    
    bot.edit_message_media(
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        media=InputMediaPhoto(BANNER_URL, caption=text, parse_mode='HTML'),
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'menu_back')
def menu_back(call):
    bot.answer_callback_query(call.id)
    name = call.from_user.first_name
    user_id = str(call.from_user.id)
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("〔 𝗧𝗼𝗼𝗹𝘀 〕", callback_data="menu_tools"),
        InlineKeyboardButton("〔 𝗣𝗿𝗼𝘅𝘆 〕", callback_data="menu_proxy")
    )
    markup.add(
        InlineKeyboardButton("〔 𝗡𝗲𝘄 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀 〕", callback_data="menu_new"),
        InlineKeyboardButton("〔 𝗗𝗲𝘃 〕", callback_data="menu_dev")
    )
    markup.add(
        InlineKeyboardButton("〔 ⭐ اشترك بالنجوم 〕", callback_data="stars_menu"),
        InlineKeyboardButton("〔 𝗣𝗿𝗼𝗳𝗶𝗹𝗲 〕", callback_data="menu_profile")
    )
    
    status = get_user_status(user_id)
    
    text = f"""<b>✦ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 {name} 𝐓𝐎 {BOT_NAME} ✦

【{em('gateway')}】 𝗚𝗔𝗧𝗘𝗪𝗔𝗬𝗦 ➛ 𝙎𝙩𝙧𝙞𝙥𝙚 + 𝘽𝙧𝙖𝙞𝙣𝙩𝙧𝙚𝙚 + 𝐏𝐚𝐲𝐏𝐚𝐥 + 𝐏𝐚𝐲𝐦𝐞𝐧𝐭𝐬.𝐀𝐈
【{em('mode')}】 𝗠𝗢𝗗𝗘 ➛ 𝘼𝙪𝙩𝙝 + 𝘾𝙝𝙖𝙧𝙜𝙚
【{em('speed')}】 𝗦𝗣𝗘𝗘𝗗 ➛ 𝙐𝙡𝙩𝙧𝙖 𝙁𝙖𝙨𝙩
【{em('status_icon')}】 𝗦𝗧𝗔𝗧𝗨𝗦 ➛ {status}
【{em('version_icon')}】 𝗩𝗘𝗥𝗦𝗜𝗢𝗡 ➛ {VERSION}

━━━━━━━━━━━━━━━━━━━━━━━━

【「{em('choose')}」】 𝗖𝗛𝗢𝗢𝗦𝗘 𝗔 𝗦𝗘𝗥𝗩𝗜𝗖𝗘 【「{em('choose')}」】</b>"""
    
    bot.edit_message_media(
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        media=InputMediaPhoto(BANNER_URL, caption=text, parse_mode='HTML'),
        reply_markup=markup
    )

# ═══════════════════════════════════════════════════════════════
# bot.py v11.0 - الجزء 4/4 (النهائي)
# ═══════════════════════════════════════════════════════════════'''
# ═══════════════════════════════════════════════════════════════
# معالجات فحص البوابات الفردية (مُصلحة بالكامل)
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data == 'check_stripe_ezy')
def check_stripe_ezy_callback(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    
    if not is_user_premium(user_id):
        bot.send_message(call.message.chat.id, f"<b>{em('error')} 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗼𝗻𝗹𝘆.\n\n{em('star')} استخدم /stars للاشتراك بالنجوم</b>", parse_mode="HTML")
        return
    
    bot.send_message(call.message.chat.id, f"<b>{em('stripe')} 𝗦𝗲𝗻𝗱 𝗰𝗮𝗿𝗱 𝗶𝗻 𝗳𝗼𝗿𝗺𝗮𝘁:\n<code>4405103045656027|10|2026|604</code></b>", parse_mode="HTML")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, stripe_check_handler)

def stripe_check_handler(message):
    user_id = str(message.from_user.id)
    cc = reg(message.text)
    if not cc:
        bot.reply_to(message, f"<b>{em('error')} 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗰𝗮𝗿𝗱 𝗳𝗼𝗿𝗺𝗮𝘁.</b>", parse_mode="HTML")
        return
    
    msg = bot.reply_to(message, f"<b>{em('stripe')} 𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗴 𝗦𝘁𝗿𝗶𝗽𝗲...</b>", parse_mode="HTML")
    
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
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('error')} 𝗘𝗿𝗿𝗼𝗿: {str(e)[:50]}</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'check_payments_ai')
def check_payments_ai_callback(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    
    if not is_user_premium(user_id):
        bot.send_message(call.message.chat.id, f"<b>{em('error')} 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗼𝗻𝗹𝘆.\n\n{em('star')} استخدم /stars للاشتراك بالنجوم</b>", parse_mode="HTML")
        return
    
    bot.send_message(call.message.chat.id, f"<b>{em('paymentsai')} 𝗦𝗲𝗻𝗱 𝗰𝗮𝗿𝗱 𝗶𝗻 𝗳𝗼𝗿𝗺𝗮𝘁:\n<code>4405103045656027|10|2026|604</code></b>", parse_mode="HTML")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, payments_ai_check_handler)

def payments_ai_check_handler(message):
    user_id = str(message.from_user.id)
    cc = reg(message.text)
    if not cc:
        bot.reply_to(message, f"<b>{em('error')} 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗰𝗮𝗿𝗱 𝗳𝗼𝗿𝗺𝗮𝘁.</b>", parse_mode="HTML")
        return
    
    msg = bot.reply_to(message, f"<b>{em('paymentsai')} 𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗴 𝗣𝗮𝘆𝗺𝗲𝗻𝘁𝘀.𝗔𝗜...</b>", parse_mode="HTML")
    
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
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('error')} 𝗘𝗿𝗿𝗼𝗿: {str(e)[:50]}</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'check_braintree')
def check_braintree_callback(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    
    if not is_user_premium(user_id):
        bot.send_message(call.message.chat.id, f"<b>{em('error')} 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗼𝗻𝗹𝘆.\n\n{em('star')} استخدم /stars للاشتراك بالنجوم</b>", parse_mode="HTML")
        return
    
    bot.send_message(call.message.chat.id, f"<b>{em('braintree')} 𝗦𝗲𝗻𝗱 𝗰𝗮𝗿𝗱 𝗶𝗻 𝗳𝗼𝗿𝗺𝗮𝘁:\n<code>4405103045656027|10|2026|604</code></b>", parse_mode="HTML")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, braintree_check_handler)

def braintree_check_handler(message):
    user_id = str(message.from_user.id)
    cc = reg(message.text)
    if not cc:
        bot.reply_to(message, f"<b>{em('error')} 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗰𝗮𝗿𝗱 𝗳𝗼𝗿𝗺𝗮𝘁.</b>", parse_mode="HTML")
        return
    
    msg = bot.reply_to(message, f"<b>{em('braintree')} 𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗴 𝗕𝗿𝗮𝗶𝗻𝘁𝗿𝗲𝗲...</b>", parse_mode="HTML")
    
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
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('error')} 𝗘𝗿𝗿𝗼𝗿: {str(e)[:50]}</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'check_paypal')
def check_paypal_callback(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    
    if not is_user_premium(user_id):
        bot.send_message(call.message.chat.id, f"<b>{em('error')} 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗼𝗻𝗹𝘆.\n\n{em('star')} استخدم /stars للاشتراك بالنجوم</b>", parse_mode="HTML")
        return
    
    bot.send_message(call.message.chat.id, f"<b>{em('paypal')} 𝗦𝗲𝗻𝗱 𝗰𝗮𝗿𝗱 𝗶𝗻 𝗳𝗼𝗿𝗺𝗮𝘁:\n<code>4405103045656027|10|2026|604</code></b>", parse_mode="HTML")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, paypal_check_handler)

def paypal_check_handler(message):
    user_id = str(message.from_user.id)
    cc = reg(message.text)
    if not cc:
        bot.reply_to(message, f"<b>{em('error')} 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗰𝗮𝗿𝗱 𝗳𝗼𝗿𝗺𝗮𝘁.</b>", parse_mode="HTML")
        return
    
    msg = bot.reply_to(message, f"<b>{em('paypal')} 𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗴 𝗣𝗮𝘆𝗣𝗮𝗹...</b>", parse_mode="HTML")
    
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
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"<b>{em('error')} 𝗘𝗿𝗿𝗼𝗿: {str(e)[:50]}</b>", parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# أوامر أخرى ومعالجات
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data == 'menu_proxy')
def menu_proxy(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"<b>{em('proxy')} 𝗦𝗲𝗻𝗱 𝗽𝗿𝗼𝘅𝘆 𝗶𝗻 𝗳𝗼𝗿𝗺𝗮𝘁:\n<code>ip:port</code> or <code>ip:port:user:pass</code></b>", parse_mode="HTML")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, proxy_handler)

def proxy_handler(message):
    proxy_str = message.text.strip()
    proxy = parse_proxy(proxy_str)
    if not proxy:
        bot.reply_to(message, f"<b>{em('error')} 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗽𝗿𝗼𝘅𝘆 𝗳𝗼𝗿𝗺𝗮𝘁</b>", parse_mode="HTML")
        return
    
    add_user_proxy(str(message.from_user.id), proxy_str)
    bot.reply_to(message, f"<b>{em('success')} 𝗣𝗿𝗼𝘅𝘆 𝗮𝗱𝗱𝗲𝗱:\n<code>{proxy_str}</code></b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'menu_dev')
def menu_dev(call):
    bot.answer_callback_query(call.id)
    text = f"""<b>{em('developer')} 𝗗𝗘𝗩𝗘𝗟𝗢𝗣𝗘𝗥 𝗜𝗡𝗙𝗢

💎 𝗗𝗲𝘃: {DEVELOPER_USERNAME}
🔧 𝗩𝗲𝗿𝘀𝗶𝗼𝗻: {VERSION}
🚀 𝗚𝗮𝘁𝗲𝘄𝗮𝘆𝘀: Stripe + Payments.AI + Braintree + PayPal
⭐ 𝗦𝘁𝗮𝗿𝘀 𝗣𝗮𝘆𝗺𝗲𝗻𝘁: 𝗔𝗰𝘁𝗶𝘃𝗲

{em('skull')} {BOT_NAME} v{VERSION}</b>"""
    bot.send_message(call.message.chat.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'menu_profile')
def menu_profile(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    status = get_user_status(user_id)
    stats = get_stats_text(user_id)
    
    text = f"""<b>{em('profile_icon')} 𝗬𝗢𝗨𝗥 𝗣𝗥𝗢𝗙𝗜𝗟𝗘

👤 𝗨𝘀𝗲𝗿 𝗜𝗗: <code>{user_id}</code>
{status}

{stats}

{em('skull')} {BOT_NAME}</b>"""
    bot.send_message(call.message.chat.id, text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# أوامر الأدمن
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['approve'])
def approve_command(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, f"<b>{em('error')} 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆.</b>", parse_mode="HTML")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"<b>{em('error')} 𝗨𝘀𝗮𝗴𝗲: <code>/approve user_id days</code></b>", parse_mode="HTML")
        return
    
    user_id = parts[1]
    days = int(parts[2]) if len(parts) > 2 else 7
    
    code = generate_code()
    expiry = datetime.now() + timedelta(days=days)
    user_codes[code] = {'user_id': user_id, 'expiry': expiry, 'type': 'admin'}
    
    try:
        user_text = f"""<b>{em('success')} 𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗜𝗢𝗡 𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗!

{em('code')} Your Code: <code>{code}</code>
{em('time')} Valid until: {expiry.strftime('%Y-%m-%d %H:%M')}
{em('unlock')} Status: 𝗣𝗥𝗘𝗠𝗜𝗨𝗠

{em('fire')} Send /start to access!</b>"""
        bot.send_message(user_id, user_text, parse_mode="HTML")
    except:
        pass
    
    bot.reply_to(message, f"<b>{em('success')} 𝗨𝘀𝗲𝗿 {user_id} 𝗮𝗽𝗽𝗿𝗼𝘃𝗲𝗱.\n{em('code')} Code: <code>{code}</code></b>", parse_mode="HTML")

@bot.message_handler(commands=['ban'])
def ban_command(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, f"<b>{em('error')} 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆.</b>", parse_mode="HTML")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"<b>{em('error')} 𝗨𝘀𝗮𝗴𝗲: <code>/ban user_id</code></b>", parse_mode="HTML")
        return
    
    user_id = parts[1]
    if user_id not in banned_users:
        banned_users.append(user_id)
    bot.reply_to(message, f"<b>{em('success')} 𝗨𝘀𝗲𝗿 {user_id} 𝗯𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")

@bot.message_handler(commands=['unban'])
def unban_command(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, f"<b>{em('error')} 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆.</b>", parse_mode="HTML")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"<b>{em('error')} 𝗨𝘀𝗮𝗴𝗲: <code>/unban user_id</code></b>", parse_mode="HTML")
        return
    
    user_id = parts[1]
    if user_id in banned_users:
        banned_users.remove(user_id)
    bot.reply_to(message, f"<b>{em('success')} 𝗨𝘀𝗲𝗿 {user_id} 𝘂𝗻𝗯𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")

@bot.message_handler(commands=['users'])
def users_command(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, f"<b>{em('error')} 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆.</b>", parse_mode="HTML")
        return
    
    total_users = len(user_stats)
    premium_users = sum(1 for code, data in user_codes.items() if data.get('type') in ['admin', 'stars'] and datetime.now() < data.get('expiry', datetime.now()))
    banned_count = len(banned_users)
    
    text = f"""<b>{em('admin_icon')} 𝗔𝗗𝗠𝗜𝗡 𝗦𝗧𝗔𝗧𝗦

👥 Total Users: {total_users}
⭐ Premium Users: {premium_users}
🚫 Banned: {banned_count}
🔑 Active Codes: {len(user_codes)}

{em('skull')} {BOT_NAME} v{VERSION}</b>"""
    bot.reply_to(message, text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# تشغيل البوت
# ═══════════════════════════════════════════════════════════════

print(f'✦ {BOT_NAME} {VERSION} 𝗥𝘂𝗻𝗻𝗶𝗻𝗴...')
print(f'💎 𝗗𝗲𝘃: {DEVELOPER_USERNAME}')
print(f'🚀 𝗚𝗮𝘁𝗲𝘄𝗮𝘆𝘀: Stripe + Payments.AI + Braintree + PayPal')
print(f'⭐ 𝗦𝘁𝗮𝗿𝘀 𝗣𝗮𝘆𝗺𝗲𝗻𝘁: Active (1 Star = 1 Day)')
print(f'🔥 𝗡𝗲𝘄 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀: /iban /identity /proxy /mass /stats /ping /export /bin /fake /check /stars')

while True:
    try: bot.infinity_polling()
    except Exception as e: print(f'❌ 𝗘𝗿𝗿𝗼𝗿: {e}'); time.sleep(5)
