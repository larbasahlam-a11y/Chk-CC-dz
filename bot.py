# ==================== bot.py - FULL WITH FONT ====================

import telebot
import time, threading, random, re
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from gateways import *

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

command_usage = {}
user_codes = {}
user_proxies = {}
banned_users = []
admin_sessions = {}
user_stats = {}
pending_activation = {}

def generate_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=4)) + '-' + ''.join(random.choices(chars, k=4)) + '-' + ''.join(random.choices(chars, k=4))

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

@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users:
        bot.reply_to(message, f"<b>{em('declined')} 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗯𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    user_code = get_user_code(user_id)
    if user_id != str(ADMIN_ID) and not is_code_valid(user_code) and user_id not in pending_activation:
        sent_message = bot.send_message(chat_id=message.chat.id, text=f"{em('welcome')} 𝗟𝗼𝗮𝗱𝗶𝗻𝗴...")
        time.sleep(1)
        name = message.from_user.first_name
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("〔 𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗔𝗰𝘁𝗶𝘃𝗮𝘁𝗶𝗼𝗻 〕", callback_data="request_activation", icon_custom_emoji_id=eid('admin_icon'), style="danger"))
        text = f"""<blockquote><b>{em('welcome')} 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 {name} 𝗧𝗢 {BOT_NAME} {em('welcome')}</b></blockquote>
<b>{em('declined')} 𝗔𝗖𝗖𝗘𝗦𝗦 𝗗𝗘𝗡𝗜𝗘𝗗</b>
<b>{em('error')} 𝗬𝗼𝘂 𝗻𝗲𝗲𝗱 𝗮𝗻 𝗮𝗰𝘁𝗶𝘃𝗮𝘁𝗶𝗼𝗻 𝗰𝗼𝗱𝗲.</b>
<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>{em('choose')} 𝗖𝗹𝗶𝗰𝗸 𝗯𝗲𝗹𝗼𝘄 𝘁𝗼 𝗿𝗲𝗾𝘂𝗲𝘀𝘁 𝗮𝗰𝗰𝗲𝘀𝘀</b>"""
        bot.edit_message_text(chat_id=message.chat.id, message_id=sent_message.message_id, text=text, reply_markup=markup, parse_mode="HTML")
        return
    
    sent_message = bot.send_message(chat_id=message.chat.id, text=f"{em('welcome')} 𝗟𝗼𝗮𝗱𝗶𝗻𝗴...")
    time.sleep(1)
    name = message.from_user.first_name
    if user_id not in user_stats: user_stats[user_id] = {'total': 0, 'charged': 0, 'funds': 0, 'ccn': 0, 'declined': 0}
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("〔  𝗧𝗼𝗼𝗹𝘀 〕", callback_data="menu_tools", icon_custom_emoji_id=eid('tools'), style="primary"))
    markup.add(InlineKeyboardButton("〔  𝗣𝗿𝗼𝘅𝘆 〕", callback_data="menu_proxy", icon_custom_emoji_id=eid('proxy'), style="success"))
    markup.add(InlineKeyboardButton("〔  𝗗𝗲𝘃 〕", callback_data="menu_dev", icon_custom_emoji_id=eid('developer'), style="danger"))
    markup.add(InlineKeyboardButton("〔  𝗣𝗿𝗼𝗳𝗶𝗹𝗲 〕", callback_data="menu_profile", icon_custom_emoji_id=eid('profile_icon'), style="primary"))
    
    text = f"""<blockquote><b>✦ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 {name} 𝐓𝐎 𝐏𝐑𝐎𝐅𝐄𝐒𝐎𝐑 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 ✦</b></blockquote>

<b>【{em('gateway')}】 𝗚𝗔𝗧𝗘𝗪𝗔𝗬𝗦 ➛ 𝙎𝙩𝙧𝙞𝙥𝙚 + 𝘽𝙧𝙖𝙞𝙣𝙩𝙧𝙚𝙚 + 𝐏𝐚𝐲𝐏𝐚𝐥 + 𝐏𝐚𝐲𝐦𝐞𝐧𝐭𝐬.𝐀𝐈</b>
<b>【{em('mode')}】 𝗠𝗢𝗗𝗘 ➛ 𝘼𝙪𝙩𝙝 + 𝘾𝙝𝙖𝙧𝙜𝙚</b>
<b>【{em('speed')}】 𝗦𝗣𝗘𝗘𝗗 ➛ 𝙐𝙡𝙩𝙧𝙖 𝙁𝙖𝙨𝙩</b>
<b>【{em('status_icon')}】 𝗦𝗧𝗔𝗧𝗨𝗦 ➛ 𝙎𝙩𝙖𝙗𝙡𝙚 + 𝙎𝙚𝙘𝙪𝙧𝙚</b>
<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>【「{em('choose')}」】 𝗖𝗛𝗢𝗢𝗦𝗘 𝗔 𝗦𝗘𝗥𝗩𝗜𝗖𝗘 【「{em('choose')}」】</b>"""
    
    bot.edit_message_text(chat_id=message.chat.id, message_id=sent_message.message_id, text=text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'menu_tools')
def menu_tools(call):
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("〔 𝐒𝐭𝐫𝐢𝐩𝐞 𝗔𝘂𝘁𝗵 〕", callback_data="check_stripe_ezy", icon_custom_emoji_id=eid('stripe'), style="primary"),
        InlineKeyboardButton("〔 𝐏𝐚𝐲𝐦𝐞𝐧𝐭𝐬.𝐀𝐈 〕", callback_data="check_payments_ai", icon_custom_emoji_id=eid('paymentsai'), style="danger")
    )
    markup.add(
        InlineKeyboardButton("〔 𝘽𝙧𝙖𝙞𝙣𝙩𝙧𝙚𝙚 〕", callback_data="check_braintree", icon_custom_emoji_id=eid('braintree'), style="success"),
        InlineKeyboardButton("〔 𝐏𝐚𝐲𝐏𝐚𝐥 𝟳$ 〕", callback_data="check_paypal", icon_custom_emoji_id=eid('paypal'), style="primary")
    )
    markup.add(InlineKeyboardButton("〔  𝗖𝗼𝗺𝗯𝗼 𝗖𝗵𝗲𝗰𝗸 〕", callback_data="check_combo", icon_custom_emoji_id=eid('combo_card'), style="success"))
    markup.add(InlineKeyboardButton("〔  𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀 〕", callback_data="menu_commands", icon_custom_emoji_id=eid('code'), style="primary"))
    markup.add(InlineKeyboardButton("〔  𝗕𝗮𝗰𝗸 〕", callback_data="menu_back", icon_custom_emoji_id=eid('back_icon'), style="danger"))
    
    text = f"<b>{em('tools')} 𝗧𝗢𝗢𝗟𝗦 𝗠𝗘𝗡𝗨\n━━━━━━━━━━━━━━━━━━━━━━━━\n{em('choose')} 𝗦𝗲𝗹𝗲𝗰𝘁 𝗮 𝗴𝗮𝘁𝗲𝘄𝗮𝘆 𝘁𝗼 𝗰𝗵𝗲𝗰𝗸 𝗰𝗮𝗿𝗱</b>"
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'menu_commands')
def menu_commands(call):
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("〔 🔙 𝗕𝗮𝗰𝗸 〕", callback_data="menu_tools", icon_custom_emoji_id=eid('back_icon'), style="danger"))
    text = f"""<b>{em('code')} 𝗖𝗢𝗠𝗠𝗔𝗡𝗗𝗦 𝗟𝗜𝗦𝗧
━━━━━━━━━━━━━━━━━━━━━━━━
{em('stripe')} <code>/chk card</code> - 𝗦𝘁𝗿𝗶𝗽𝗲 𝗔𝘂𝘁𝗵
{em('paymentsai')} <code>/pai card</code> - 𝗣𝗮𝘆𝗺𝗲𝗻𝘁𝘀.𝗔𝗜
{em('braintree')} <code>/bt card</code> - 𝗕𝗿𝗮𝗶𝗻𝘁𝗿𝗲𝗲 𝗔𝘂𝘁𝗵
{em('paypal')} <code>/pp card</code> - 𝗣𝗮𝘆𝗣𝗮𝗹 𝟳$
━━━━━━━━━━━━━━━━━━━━━━━━
 𝗙𝗼𝗿𝗺𝗮𝘁: <code>4405103045656027|10|2026|604</code></b>"""
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'check_stripe_ezy')
def stripe_ezy_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"<b>{em('stripe')} 𝗦𝘁𝗿𝗶𝗽𝗲 𝗔𝘂𝘁𝗵\n\n 𝗦𝗲𝗻𝗱 𝗖𝗮𝗿𝗱:\n<code>4405103045656027|10|2026|604</code>\n\n 𝗢𝗿: /chk card</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'check_payments_ai')
def payments_ai_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"<b>{em('paymentsai')} 𝗣𝗮𝘆𝗺𝗲𝗻𝘁𝘀.𝗔𝗜\n\n 𝗦𝗲𝗻𝗱 𝗖𝗮𝗿𝗱:\n<code>4405103045656027|10|2026|604</code>\n\n 𝗢𝗿: /pai card</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'check_braintree')
def braintree_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"<b>{em('braintree')} 𝗕𝗿𝗮𝗶𝗻𝘁𝗿𝗲𝗲 𝗔𝘂𝘁𝗵\n\n 𝗦𝗲𝗻𝗱 𝗖𝗮𝗿𝗱:\n<code>4405103045656027|10|2026|604</code>\n\n 𝗢𝗿: /bt card</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'check_paypal')
def paypal_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"<b>{em('paypal')} 𝗣𝗮𝘆𝗣𝗮𝗹 𝟳$\n\n 𝗦𝗲𝗻𝗱 𝗖𝗮𝗿𝗱:\n<code>4405103045656027|10|2026|604</code>\n\n 𝗢𝗿: /pp card</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'check_combo')
def combo_check_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"<b>{em('combo_card')} 𝗖𝗢𝗠𝗕𝗢 𝗖𝗛𝗘𝗖𝗞𝗘𝗥\n\n 𝗦𝗲𝗻𝗱 𝗮 .txt 𝗳𝗶𝗹𝗲\n𝗙𝗼𝗿𝗺𝗮𝘁: <code>card|mm|yy|cvv</code></b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'menu_proxy')
def menu_proxy(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    proxies = user_proxies.get(user_id, [])
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("〔  𝗔𝗱𝗱 𝗣𝗿𝗼𝘅𝘆 〕", callback_data="add_proxy_menu", icon_custom_emoji_id=eid('funds'), style="primary"))
    markup.add(InlineKeyboardButton("〔  𝗠𝘆 𝗣𝗿𝗼𝘅𝗶𝗲𝘀 〕", callback_data="list_proxies", icon_custom_emoji_id=eid('proxy'), style="success"))
    markup.add(InlineKeyboardButton("〔  𝗖𝗹𝗲𝗮𝗿 〕", callback_data="clear_proxies", icon_custom_emoji_id=eid('declined'), style="danger"))
    markup.add(InlineKeyboardButton("〔  𝗕𝗮𝗰𝗸 〕", callback_data="menu_back", icon_custom_emoji_id=eid('back_icon'), style="danger"))
    text = f"<b>{em('proxy')} 𝗣𝗥𝗢𝗫𝗬 𝗠𝗘𝗡𝗨\n━━━━━━━━━━━━━━━━━━━━━━━━\n{em('funds')} 𝗧𝗼𝘁𝗮𝗹: {len(proxies)}</b>"
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'menu_dev')
def menu_dev(call):
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("〔  𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗗𝗲𝘃 〕", url=f"https://t.me/{DEVELOPER_USERNAME.replace('@','')}", icon_custom_emoji_id=eid('developer'), style="primary"))
    if call.from_user.id == ADMIN_ID:
        markup.add(InlineKeyboardButton("〔 𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 〕", callback_data="admin_broadcast", icon_custom_emoji_id=eid('proxy'), style="success"))
        markup.add(InlineKeyboardButton("〔  𝗔𝗱𝗺𝗶𝗻 〕", callback_data="admin_menu", icon_custom_emoji_id=eid('admin_icon'), style="danger"))
    markup.add(InlineKeyboardButton("〔  𝗕𝗮𝗰𝗸 〕", callback_data="menu_back", icon_custom_emoji_id=eid('back_icon'), style="danger"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text=f"<b>{em('developer')} 𝗗𝗘𝗩 𝗠𝗘𝗡𝗨\n━━━━━━━━━━━━━━━━━━━━━━━━\n{em('skull')} {DEVELOPER_USERNAME}</b>", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'admin_menu')
def admin_menu_callback(call):
    if call.from_user.id != ADMIN_ID: return
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("〔  𝗦𝘁𝗮𝘁𝘀 〕", callback_data="admin_stats", icon_custom_emoji_id=eid('stats'), style="primary"))
    markup.add(InlineKeyboardButton("〔  𝗖𝗿𝗲𝗮𝘁𝗲 𝗖𝗼𝗱𝗲 〕", callback_data="admin_create_code", icon_custom_emoji_id=eid('code'), style="success"))
    markup.add(InlineKeyboardButton("〔  𝗕𝗮𝗻 𝗨𝘀𝗲𝗿 〕", callback_data="admin_ban_menu", icon_custom_emoji_id=eid('declined'), style="danger"))
    markup.add(InlineKeyboardButton("〔  𝗕𝗮𝗰𝗸 〕", callback_data="menu_dev", icon_custom_emoji_id=eid('back_icon'), style="danger"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text=f"<b>{em('admin_icon')} 𝗔𝗗𝗠𝗜𝗡</b>", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'menu_profile')
def menu_profile(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    code = get_user_code(user_id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("〔  𝗦𝘁𝗮𝘁𝘀 〕", callback_data="user_stats", icon_custom_emoji_id=eid('stats'), style="primary"))
    markup.add(InlineKeyboardButton("〔  𝗠𝘆 𝗖𝗼𝗱𝗲 〕", callback_data="user_code", icon_custom_emoji_id=eid('code'), style="success"))
    markup.add(InlineKeyboardButton("〔  𝗕𝘂𝘆 𝗔𝗰𝘁𝗶𝘃𝗮𝘁𝗶𝗼𝗻 〕", callback_data="buy_activation", icon_custom_emoji_id=eid('charged'), style="primary"))
    markup.add(InlineKeyboardButton("〔  𝗕𝗮𝗰𝗸 〕", callback_data="menu_back", icon_custom_emoji_id=eid('back_icon'), style="danger"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text=f"<b>{em('profile_icon')} 𝗣𝗥𝗢𝗙𝗜𝗟𝗘\n━━━━━━━━━━━━━━━━━━━━━━━━\n{em('code')} 𝗖𝗼𝗱𝗲: {code if code else '𝗡𝗼𝗻𝗲'}</b>", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'buy_activation')
def buy_activation(call):
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("〔  𝟱𝟬 𝗦𝘁𝗮𝗿𝘀 - 𝟭𝗠 〕", callback_data="pay_50", icon_custom_emoji_id=eid('charged'), style="primary"))
    markup.add(InlineKeyboardButton("〔  𝟭𝟬𝟬 𝗦𝘁𝗮𝗿𝘀 - 𝟯𝗠 〕", callback_data="pay_100", icon_custom_emoji_id=eid('charged'), style="success"))
    markup.add(InlineKeyboardButton("〔  𝟮𝟬𝟬 𝗦𝘁𝗮𝗿𝘀 - 𝗟𝗶𝗳𝗲 〕", callback_data="pay_200", icon_custom_emoji_id=eid('charged'), style="primary"))
    markup.add(InlineKeyboardButton("〔 🔙 𝗕𝗮𝗰𝗸 〕", callback_data="menu_profile", icon_custom_emoji_id=eid('back_icon'), style="danger"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text=f"<b>{em('charged')} 𝗕𝗨𝗬 𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗜𝗢𝗡</b>", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'menu_back')
def menu_back(call):
    bot.answer_callback_query(call.id)
    name = call.from_user.first_name
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("〔  𝗧𝗼𝗼𝗹𝘀 〕", callback_data="menu_tools", icon_custom_emoji_id=eid('tools'), style="primary"))
    markup.add(InlineKeyboardButton("〔  𝗣𝗿𝗼𝘅𝘆 〕", callback_data="menu_proxy", icon_custom_emoji_id=eid('proxy'), style="success"))
    markup.add(InlineKeyboardButton("〔  𝗗𝗲𝘃 〕", callback_data="menu_dev", icon_custom_emoji_id=eid('developer'), style="danger"))
    markup.add(InlineKeyboardButton("〔  𝗣𝗿𝗼𝗳𝗶𝗹𝗲 〕", callback_data="menu_profile", icon_custom_emoji_id=eid('profile_icon'), style="primary"))
    
    text = f"""<blockquote><b>✦ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 {name} 𝐓𝐎 𝐏𝐑𝐎𝐅𝐄𝐒𝐎𝐑 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 ✦</b></blockquote>

<b>【{em('gateway')}】 𝗚𝗔𝗧𝗘𝗪𝗔𝗬𝗦 ➛ 𝙎𝙩𝙧𝙞𝙥𝙚 + 𝘽𝙧𝙖𝙞𝙣𝙩𝙧𝙚𝙚 + 𝐏𝐚𝐲𝐏𝐚𝐥 + 𝐏𝐚𝐲𝐦𝐞𝐧𝐭𝐬.𝐀𝐈</b>
<b>【{em('mode')}】 𝗠𝗢𝗗𝗘 ➛ 𝘼𝙪𝙩𝙝 + 𝘾𝙝𝙖𝙧𝙜𝙚</b>
<b>【{em('speed')}】 𝗦𝗣𝗘𝗘𝗗 ➛ 𝙐𝙡𝙩𝙧𝙖 𝙁𝙖𝙨𝙩</b>
<b>【{em('status_icon')}】 𝗦𝗧𝗔𝗧𝗨𝗦 ➛ 𝙎𝙩𝙖𝙗𝙡𝙚 + 𝙎𝙚𝙘𝙪𝙧𝙚</b>
<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>【「{em('choose')}」】 𝗖𝗛𝗢𝗢𝗦𝗘 𝗔 𝗦𝗘𝗥𝗩𝗜𝗖𝗘 【「{em('choose')}」】</b>"""
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'user_stats')
def stats_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, get_stats_text(str(call.from_user.id)), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'user_code')
def code_callback(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    code = get_user_code(user_id)
    if code:
        bot.send_message(call.message.chat.id, f"<b>{em('code')} 𝗖𝗼𝗱𝗲:\n\n<code>{code}</code></b>", parse_mode="HTML")
    else:
        bot.send_message(call.message.chat.id, f"<b>{em('code')} 𝗡𝗼 𝗰𝗼𝗱𝗲. 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗮𝗱𝗺𝗶𝗻.</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'request_activation')
def request_activation(call):
    bot.answer_callback_query(call.id, "𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝘀𝗲𝗻𝘁!", show_alert=True)
    user_id = str(call.from_user.id)
    pending_activation[user_id] = {'name': call.from_user.first_name, 'username': call.from_user.username or 'N/A', 'time': datetime.now()}
    bot.send_message(ADMIN_ID, f"<b>{em('admin_icon')} 𝗡𝗘𝗪 𝗥𝗘𝗤𝗨𝗘𝗦𝗧\n{em('developer')} {call.from_user.first_name}\n{em('code')} <code>{user_id}</code>\n/activate {user_id}</b>", parse_mode="HTML")
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"<b>{em('funds')} 𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝘀𝗲𝗻𝘁!</b>", parse_mode="HTML")

@bot.message_handler(commands=["activate"])
def activate_user(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split()
    if len(parts) < 2: bot.reply_to(message, f"<b>{em('error')} /activate user_id</b>", parse_mode="HTML"); return
    target_id = parts[1]
    code = generate_code()
    user_codes[code] = {'user_id': target_id, 'created': datetime.now(), 'expiry': None, 'used': 0}
    if target_id in pending_activation: del pending_activation[target_id]
    try:
        bot.send_message(int(target_id), f"<b>{em('charged')} 𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗘𝗗!\n{em('code')} <code>{code}</code></b>", parse_mode="HTML")
        bot.reply_to(message, f"<b>{em('funds')} 𝗗𝗼𝗻𝗲!</b>", parse_mode="HTML")
    except: bot.reply_to(message, f"<b>{em('declined')} 𝗙𝗮𝗶𝗹𝗲𝗱.</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'add_proxy_menu')
def add_proxy_menu_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"<b>{em('proxy')} 𝗦𝗘𝗡𝗗 𝗣𝗥𝗢𝗫𝗬:\n\n<code>ip:port</code>\nor\n<code>ip:port:user:pass</code></b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'list_proxies')
def list_proxies_callback(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    proxies = user_proxies.get(user_id, [])
    if proxies:
        text = f"<b>{em('proxy')} 𝗬𝗢𝗨𝗥 𝗣𝗥𝗢𝗫𝗜𝗘𝗦:</b>\n\n"
        for i, p in enumerate(proxies[:20], 1): text += f"<code>{i}. {str(p)[:50]}...</code>\n"
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")
    else: bot.send_message(call.message.chat.id, f"<b>{em('error')} 𝗡𝗼 𝗽𝗿𝗼𝘅𝗶𝗲𝘀.</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'clear_proxies')
def clear_proxies_callback(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    user_proxies[user_id] = []
    bot.send_message(call.message.chat.id, f"<b>{em('declined')} 𝗖𝗹𝗲𝗮𝗿𝗲𝗱!</b>", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and re.match(r'^\d+\.\d+\.\d+\.\d+:\d+', m.text.strip()))
def receive_proxy(message):
    user_id = str(message.from_user.id)
    lines = message.text.strip().split('\n')
    added = sum(1 for line in lines if add_user_proxy(user_id, line.strip()))
    bot.reply_to(message, f"<b>{em('funds')} 𝗔𝗱𝗱𝗲𝗱 {added} 𝗽𝗿𝗼𝘅𝘆(s)!</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'admin_stats')
def admin_stats_callback(call):
    if call.from_user.id != ADMIN_ID: return
    total_users = len(user_stats); total_checks = sum(s['total'] for s in user_stats.values())
    total_charged = sum(s['charged'] for s in user_stats.values()); total_funds = sum(s['funds'] for s in user_stats.values())
    total_ccn = sum(s['ccn'] for s in user_stats.values()); total_declined = sum(s['declined'] for s in user_stats.values())
    bot.send_message(call.message.chat.id, f"""<b>{em('stats')} 𝗕𝗢𝗧 𝗦𝗧𝗔𝗧𝗦
{em('gateway')} 𝗨𝘀𝗲𝗿𝘀: {total_users} | {em('funds')} 𝗖𝗵𝗲𝗰𝗸𝘀: {total_checks}
{em('charged')} 𝗖𝗵𝗮𝗿𝗴𝗲𝗱: {total_charged} | {em('funds')} 𝗙𝘂𝗻𝗱𝘀: {total_funds}
{em('ccn')} 𝗖𝗖𝗡: {total_ccn} | {em('declined')} 𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱: {total_declined}
{em('code')} 𝗖𝗼𝗱𝗲𝘀: {len(user_codes)}</b>""", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'admin_create_code')
def admin_create_code_callback(call):
    if call.from_user.id != ADMIN_ID: return
    code = generate_code()
    user_codes[code] = {'user_id': 'admin', 'created': datetime.now(), 'expiry': None, 'used': 0}
    bot.send_message(call.message.chat.id, f"<b>{em('code')} <code>{code}</code></b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'admin_ban_menu')
def admin_ban_menu_callback(call):
    if call.from_user.id != ADMIN_ID: return
    bot.send_message(call.message.chat.id, f"<b>{em('declined')} 𝗦𝗲𝗻𝗱 𝘂𝘀𝗲𝗿 𝗜𝗗:</b>", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and m.text.isdigit() and len(m.text) > 5 and m.from_user.id == ADMIN_ID)
def ban_user(message):
    user_id = message.text.strip()
    if user_id not in banned_users: banned_users.append(user_id); bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱!</b>", parse_mode="HTML")
    else: banned_users.remove(user_id); bot.reply_to(message, f"<b>{em('funds')} 𝗨𝗻𝗯𝗮𝗻𝗻𝗲𝗱!</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == 'admin_broadcast')
def admin_broadcast_callback(call):
    if call.from_user.id != ADMIN_ID: return
    bot.send_message(call.message.chat.id, f"<b>{em('proxy')} 𝗦𝗲𝗻𝗱 𝗺𝗲𝘀𝘀𝗮𝗴𝗲:</b>", parse_mode="HTML")
    admin_sessions[str(call.from_user.id)] = 'broadcast'

@bot.message_handler(func=lambda m: str(m.from_user.id) in admin_sessions and admin_sessions[str(m.from_user.id)] == 'broadcast')
def broadcast_message(message):
    if message.from_user.id != ADMIN_ID: return
    del admin_sessions[str(message.from_user.id)]
    sent = 0
    for uid in list(user_stats.keys())[:50]:
        try: bot.send_message(int(uid), f"<b>{em('proxy')} 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧:\n\n{message.text}</b>", parse_mode="HTML"); sent += 1
        except: pass
        time.sleep(0.5)
    bot.reply_to(message, f"<b>{em('funds')} 𝗦𝗲𝗻𝘁: {sent}</b>", parse_mode="HTML")

def do_check(message, gateway_name, gateway_func, command_name, price, emoji_key):
    user_id = str(message.from_user.id); idt = message.from_user.id
    if user_id in banned_users: bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML"); return
    try: command_usage[idt]['last_time']
    except: command_usage[idt] = {'last_time': datetime.now()}
    if command_usage[idt]['last_time'] is not None:
        time_diff = (datetime.now() - command_usage[idt]['last_time']).seconds
        if time_diff < 8: bot.reply_to(message, f"<b>{em('speed')} 𝗪𝗮𝗶𝘁 {8-time_diff}s</b>", parse_mode="HTML"); return
    ko = bot.reply_to(message, f"<b>{em('speed')} 𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗴...</b>", parse_mode="HTML").message_id
    try: cc = message.reply_to_message.text
    except: cc = message.text
    cc = str(reg(cc))
    if cc == 'None': bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text=f"<b>{em('declined')} 𝗜𝗻𝘃𝗮𝗹𝗶𝗱</b>", parse_mode="HTML"); return
    start_time = time.time()
    command_usage[idt]['last_time'] = datetime.now()
    try: last = str(gateway_func(cc))
    except Exception as e: last = f'𝗘𝗿𝗿𝗼𝗿: {str(e)[:30]}'
    execution_time = time.time() - start_time
    if any(x in last for x in ['CHARGE', 'APPROVED', 'succeeded', 'accessToken']): status = f'𝗖𝗛𝗔𝗥𝗚𝗘𝗗! {em("charged")}'
    elif any(x in last for x in ['insufficient', 'Funds', 'INSUFFICIENT']): status = f'𝗙𝘂𝗻𝗱𝘀! {em("funds")}'
    elif any(x in last for x in ['security', 'CCN', 'INVALID_SECURITY_CODE']): status = f'𝗖𝗖𝗡! {em("ccn")}'
    elif any(x in last for x in ['Risk', 'RISK']): status = f'𝗥𝗜𝗦𝗞 {em("error")}'
    elif any(x in last for x in ['Error', 'Failed', 'Down']): status = f'𝗘𝗥𝗥𝗢𝗥 {em("error")}'
    else: status = f'𝗗𝗘𝗖𝗟𝗜𝗡𝗘𝗗! {em("declined")}'
    update_stats(user_id, last)
    msg = f"""<strong>[ϟ] 𝗚𝗮𝘁𝗲𝘄𝗮𝘆: {gateway_name} [ /{command_name} ]
-------------------------------
[ϟ] 𝗖𝗮𝗿𝗱: {cc} {em(emoji_key)}
[ϟ] 𝗦𝘁𝗮𝘁𝘂𝘀: {status}
[ϟ] 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: {last}
-------------------------------
{str(dato(cc[:6]))}
-------------------------------
[ϟ] 𝗧𝗶𝗺𝗲: {execution_time:.2f}s {em('speed')}
[ϟ] 𝗣𝗿𝗶𝗰𝗲: {price}
[ϟ] 𝗕𝘆: {BOT_NAME}
-------------------------------
[ϟ] 𝗗𝗲𝘃: {DEVELOPER_USERNAME} - {em('skull')}</strong>"""
    try: bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text=msg, parse_mode="HTML")
    except: bot.send_message(message.chat.id, msg, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith(('.chk', '/chk')))
def stripe_check(message): do_check(message, "𝐒𝐭𝐫𝐢𝐩𝐞 𝐀𝐮𝐭𝐡", xst_stripe_ezy, "chk", "𝗙𝗿𝗲𝗲", 'stripe')

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith(('.pai', '/pai')))
def payments_ai_check(message): do_check(message, "𝐏𝐚𝐲𝐦𝐞𝐧𝐭𝐬.𝐀𝐈", xst_payments_ai, "pai", "𝗙𝗿𝗲𝗲", 'paymentsai')

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith(('.bt', '/bt')))
def braintree_check(message): do_check(message, "𝘽𝙧𝙖𝙞𝙣𝙩𝙧𝙚𝙚 𝐀𝐮𝐭𝐡", xst_bt_dna, "bt", "𝗙𝗿𝗲𝗲", 'braintree')

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith(('.pp', '/pp')))
def paypal_check(message): do_check(message, "𝐏𝐚𝐲𝐏𝐚𝐥 𝟳$", xst_paypal_brass, "pp", "$7.00", 'paypal')

@bot.message_handler(content_types=('document'))
def combo_file(message):
    user_id = str(message.from_user.id)
    if user_id in banned_users: bot.reply_to(message, f"<b>{em('declined')} 𝗕𝗮𝗻𝗻𝗲𝗱.</b>", parse_mode="HTML"); return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        filename = f"com{user_id}.txt"
        with open(filename, "wb") as f: f.write(downloaded)
        with open(filename, 'r') as f: total = len(f.readlines())
        bts = InlineKeyboardMarkup()
        bts.add(InlineKeyboardButton("〔 𝐒𝐭𝐫𝐢𝐩𝐞 〕", callback_data='combo_stripe', icon_custom_emoji_id=eid('stripe'), style="primary"))
        bts.add(InlineKeyboardButton("〔 𝐏𝐚𝐲𝐦𝐞𝐧𝐭𝐬.𝐀𝐈 〕", callback_data='combo_pai', icon_custom_emoji_id=eid('paymentsai'), style="danger"))
        bts.add(InlineKeyboardButton("〔 𝘽𝙧𝙖𝙞𝙣𝙩𝙧𝙚𝙚 〕", callback_data='combo_bt', icon_custom_emoji_id=eid('braintree'), style="success"))
        bts.add(InlineKeyboardButton("〔 𝐏𝐚𝐲𝐏𝐚𝐥 〕", callback_data='combo_paypal', icon_custom_emoji_id=eid('paypal'), style="primary"))
        bts.add(InlineKeyboardButton("〔 𝗖𝗮𝗻𝗰𝗲𝗹 〕", callback_data='combo_cancel', icon_custom_emoji_id=eid('declined'), style="danger"))
        bot.reply_to(message, f"<b>{em('funds')} 𝗙𝗶𝗹𝗲: {total} 𝗰𝗮𝗿𝗱𝘀\n\n{em('choose')} 𝗦𝗲𝗹𝗲𝗰𝘁 𝗚𝗮𝘁𝗲𝘄𝗮𝘆:</b>", reply_markup=bts, parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"<b>{em('declined')} 𝗘𝗿𝗿𝗼𝗿: {e}</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data in ['combo_stripe', 'combo_pai', 'combo_bt', 'combo_paypal', 'combo_cancel'])
def combo_processing(call):
    gateways = {
        'combo_stripe': ('𝐒𝐭𝐫𝐢𝐩𝐞', xst_stripe_ezy),
        'combo_pai': ('𝐏𝐚𝐲𝐦𝐞𝐧𝐭𝐬.𝐀𝐈', xst_payments_ai),
        'combo_bt': ('𝘽𝙧𝙖𝙞𝙣𝙩𝙧𝙚𝙚', xst_bt_dna),
        'combo_paypal': ('𝐏𝐚𝐲𝐏𝐚𝐥', xst_paypal_brass)
    }
    if call.data == 'combo_cancel':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
            text=f"<b>{em('declined')} 𝗖𝗮𝗻𝗰𝗲𝗹𝗹𝗲𝗱.</b>", parse_mode="HTML")
        return
    
    gateway, func = gateways[call.data]
    user_id = str(call.from_user.id)
    filename = f"com{user_id}.txt"
    
    def process():
        charged, funds, ccn, declined, errors = 0, 0, 0, 0, 0
        with open(filename, 'r') as file:
            lines = file.readlines()
            total = len(lines)
            
            result_markup = InlineKeyboardMarkup(row_width=4)
            result_markup.add(
                InlineKeyboardButton(f"✅ {charged}", callback_data="noop", style="success"),
                InlineKeyboardButton(f"💳 {ccn}", callback_data="noop", style="primary"),
                InlineKeyboardButton(f"❌ {declined}", callback_data="noop", style="danger"),
                InlineKeyboardButton(f"⚠️ {errors}", callback_data="noop", style="danger")
            )
            
            progress_msg = bot.send_message(call.from_user.id,
                f"<b>{em('speed')} 𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 {gateway}... 0/{total}</b>",
                reply_markup=result_markup, parse_mode="HTML")
            
            for i, cc in enumerate(lines, 1):
                cc = cc.strip()
                try: result = str(func(cc))
                except: result = "𝗘𝗥𝗥𝗢𝗥"; errors += 1
                
                if any(x in result for x in ['CHARGE', 'APPROVED', 'succeeded', 'accessToken']): charged += 1
                elif any(x in result for x in ['insufficient', 'Funds', 'INSUFFICIENT']): funds += 1
                elif any(x in result for x in ['security', 'CCN', 'INVALID_SECURITY_CODE']): ccn += 1
                elif any(x in result for x in ['Error', 'Failed', 'Down', 'Risk']): errors += 1
                else: declined += 1
                
                if i % 5 == 0 or i == total:
                    result_markup = InlineKeyboardMarkup(row_width=4)
                    result_markup.add(
                        InlineKeyboardButton(f" {charged}", callback_data="noop", style="success"),
                        InlineKeyboardButton(f" {ccn}", callback_data="noop", style="primary"),
                        InlineKeyboardButton(f" {declined}", callback_data="noop", style="danger"),
                        InlineKeyboardButton(f" {errors}", callback_data="noop", style="danger")
                    )
                    try:
                        bot.edit_message_text(
                            chat_id=call.from_user.id, message_id=progress_msg.message_id,
                            text=f"<b>{em('speed')} 𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 {gateway}... {i}/{total}</b>",
                            reply_markup=result_markup, parse_mode="HTML")
                    except: pass
                time.sleep(9)
        
        result_markup = InlineKeyboardMarkup(row_width=4)
        result_markup.add(
            InlineKeyboardButton(f" {charged+funds+ccn}", callback_data="noop", style="success"),
            InlineKeyboardButton(f" {ccn}", callback_data="noop", style="primary"),
            InlineKeyboardButton(f" {declined}", callback_data="noop", style="danger"),
            InlineKeyboardButton(f"⚠️ {errors}", callback_data="noop", style="danger")
        )
        bot.send_message(call.from_user.id,
            f"""<strong>{em('charged')} 𝗖𝗢𝗠𝗕𝗢 𝗥𝗘𝗦𝗨𝗟𝗧𝗦
━━━━━━━━━━━━━━━━━━━━━━━━
{em('gateway')} 𝗚𝗔𝗧𝗘𝗪𝗔𝗬 ➛ {gateway}
━━━━━━━━━━━━━━━━━━━━━━━━
{em('charged')} 𝗖𝗛𝗔𝗥𝗚𝗘𝗗 ➛ {charged}
{em('funds')} 𝗙𝗨𝗡𝗗𝗦 ➛ {funds}
{em('ccn')} 𝗖𝗖𝗡 ➛ {ccn}
{em('declined')} 𝗗𝗘𝗖𝗟𝗜𝗡𝗘𝗗 ➛ {declined}
{em('error')} 𝗘𝗥𝗥𝗢𝗥𝗦 ➛ {errors}
━━━━━━━━━━━━━━━━━━━━━━━━
{em('funds')} 𝗧𝗢𝗧𝗔𝗟 ➛ {charged+funds+ccn+declined+errors}/{total}
{em('skull')} 𝗕𝘆: {BOT_NAME}</strong>""",
            reply_markup=result_markup, parse_mode="HTML")
    
    threading.Thread(target=process).start()

@bot.message_handler(commands=["dev"])
def dev_command(message):
    bot.send_message(message.chat.id, f"""<b>{em('developer')} 𝗗𝗘𝗩𝗘𝗟𝗢𝗣𝗘𝗥
{em('skull')} {DEVELOPER_USERNAME}
{em('charged')} {BOT_NAME} {VERSION}
{em('paypal')} 𝟰 𝗚𝗮𝘁𝗲𝘄𝗮𝘆𝘀
 <a href="https://t.me/{DEVELOPER_USERNAME.replace('@','')}">𝗖𝗼𝗻𝘁𝗮𝗰𝘁</a></b>""", parse_mode="HTML", disable_web_page_preview=True)

print(f'✦ {BOT_NAME} {VERSION} 𝗥𝘂𝗻𝗻𝗶𝗻𝗴...')
print(f'💎 𝗗𝗲𝘃: {DEVELOPER_USERNAME}')
print(f'🚀 𝗚𝗮𝘁𝗲𝘄𝗮𝘆𝘀: Stripe + Payments.AI + Braintree + PayPal')

while True:
    try: bot.infinity_polling()
    except Exception as e: print(f'❌ 𝗘𝗿𝗿𝗼𝗿: {e}'); time.sleep(5)
