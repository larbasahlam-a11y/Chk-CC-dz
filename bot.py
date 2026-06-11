import telebot
import requests
from datetime import datetime
import time

TOKEN = "8250378472:AAFH_JgQVbOUnCUvYQaOnLMnrWi4G_MCDZYا"  # ⚠️ غير هذا

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ========== [ إيموجيات مخصصة ] ==========
EMOJI = {
    "🖱": "5807434617627614035",
    "👏": "5809659496586288132",
    "🚬": "5809811602853075926",
    "👍": "5807579808997056157",
    "👑": "5809896295313185619",
    "✅": "5810074326002572153",
    "🌊": "5807566632037392423",
    "❤️‍🔥": "5807734762827160751",
    "🌟": "5807752668545817543",
    "👨‍💻": "5810058980084423714",
    "🔤": "5807836562142010705",
    "⬅️": "5807915142863659331",
    "➡️": "5809782886701734154",
    "✔️": "5809863662151670649",
    "💩": "5809747302897688433",
    "💀": "5807914683302157580",
    "👁": "5807579482579542638",
    "♾": "5809689694501345918",
    "👍2": "5809769340374885538",
}

def e(emoji_char):
    """إدراج إيموجي مخصص <tg-emoji>"""
    emoji_id = EMOJI.get(emoji_char)
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{emoji_char}</tg-emoji>'
    return emoji_char

# ========== [ دوال التنسيق ] ==========
def bold(text):
    return f"<b>{text}</b>"

def italic(text):
    return f"<i>{text}</i>"

def quote(text):
    return f"<blockquote>{text}</blockquote>"

def strikethrough(text):
    return f"<s>{text}</s>"

def code(text):
    return f"<code>{text}</code>"

def tamteet(text):
    if len(text) <= 1:
        return text
    return "ـ".join(list(text))

# ========== [ حالة المستخدمين ] ==========
user_state = {}
saved_tokens = {}

# ========== [ القائمة الرئيسية ] ==========
def main_menu():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(f"{e('🔤')} فحص توكن {e('🔤')}", f"{e('✅')} إحصائيات {e('✅')}")
    kb.add(f"{e('❓')} مساعدة {e('❓')}", f"{e('🌟')} تنسيقات {e('🌟')}")
    return kb

# ========== [ أزرار العمليات ] ==========
def arsenal_menu():
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        telebot.types.InlineKeyboardButton("📸 تغيير الصورة", callback_data="change_photo"),
        telebot.types.InlineKeyboardButton("✏️ تغيير الاسم", callback_data="change_name"),
    )
    kb.add(
        telebot.types.InlineKeyboardButton("🔄 إعادة فحص", callback_data="recheck_token"),
        telebot.types.InlineKeyboardButton("🗑️ مسح الصورة", callback_data="delete_photo"),
    )
    return kb

# ========== [ فحص التوكن ] ==========
def validate_token(token):
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if r.status_code == 200 and r.json().get("ok"):
            d = r.json()["result"]
            return {
                "valid": True,
                "username": d.get("username", "غير محدد"),
                "first_name": d.get("first_name", "غير محدد"),
                "id": d.get("id", "غير محدد"),
                "can_join_groups": d.get("can_join_groups", False),
                "can_read_all_group_messages": d.get("can_read_all_group_messages", False),
                "supports_inline_queries": d.get("supports_inline_queries", False),
            }
        return {"valid": False, "error": "التوكن غير صحيح"}
    except Exception as ex:
        return {"valid": False, "error": f"خطأ: {ex}"}

def decode_bot_id(bot_id):
    try:
        ts = (int(bot_id) >> 32) + 1293840000
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "غير محدد"

# ========== [ البداية ] ==========
@bot.message_handler(commands=['start'])
def start(msg):
    user_state[msg.from_user.id] = None
    welcome = (
        f"{e('👑')} {bold('أهلاً بك في بوت الذئب الأبيض')} {e('👑')}\n\n"
        f"{bold('المطور:')} @j49_c\n"
        f"{bold('الميزات:')}\n"
        f"• {e('🔤')} فحص توكنات البوتات\n"
        f"• استخراج بيانات كاملة\n"
        f"• {e('👨‍💻')} تغيير اسم وصورة البوت\n"
        f"• {e('✅')} تنسيقات متقدمة (تغليظ، اقتباس، تمطيط)\n\n"
        f"{quote('جاهز للبدء؟ اضغط على فحص توكن')}"
    )
    bot.send_message(msg.chat.id, welcome, reply_markup=main_menu())

# ========== [ معالجة النصوص ] ==========
@bot.message_handler(func=lambda m: True)
def handle_text(msg):
    uid = msg.from_user.id
    text = msg.text

    if text.startswith(f"{e('🔤')} فحص توكن") or text == "/check":
        user_state[uid] = "waiting_token"
        bot.send_message(msg.chat.id, 
            f"{bold('🔑 أرسل التوكن المستهدف:')}\n"
            f"<code>123456789:ABCDEF...</code>",
            reply_markup=telebot.types.ReplyKeyboardRemove())

    elif text.startswith(f"{e('✅')} إحصائيات") or text == "/stats":
        stats = (
            f"{bold('📊 الإحصائيات:')}\n\n"
            f"👥 المستخدمون: {len(user_state)}\n"
            f"🔑 التوكنات: {len(saved_tokens)}\n"
            f"{quote('لا تشارك التوكنات مع أحد')}"
        )
        bot.send_message(msg.chat.id, stats, reply_markup=main_menu())

    elif text.startswith(f"{e('❓')} مساعدة") or text == "/help":
        help_text = (
            f"{bold('❓ المساعدة:')}\n\n"
            f"• {e('🔤')} فحص توكن\n"
            f"• 📸 تغيير صورة البوت\n"
            f"• ✏️ تغيير اسم البوت\n\n"
            f"{bold('تنسيقات:')}\n"
            f"{bold('تغليظ')} | {italic('مائل')} | {strikethrough('تشطير')}\n"
            f"{code('كود')} | {quote('اقتباس')}\n\n"
            f"{bold('تمطيط:')} أرسل <code>مط مرحبا</code>"
        )
        bot.send_message(msg.chat.id, help_text, reply_markup=main_menu())

    elif text.startswith(f"{e('🌟')} تنسيقات") or text == "/format":
        sample = (
            f"{bold('✅ تغليظ')}\n"
            f"{italic('✅ مائل')}\n"
            f"{strikethrough('✅ تشطير')}\n"
            f"{code('✅ كود')}\n"
            f"{quote('✅ اقتباس')}\n\n"
            f"{bold('📝 تمطيط:')} {tamteet('مرحباً بكم')}"
        )
        bot.send_message(msg.chat.id, sample, reply_markup=main_menu())

    elif text.startswith("مط "):
        original = text[3:].strip()
        if original:
            bot.send_message(msg.chat.id, f"{bold('📝 النص الممطوط:')}\n{tamteet(original)}")

    elif user_state.get(uid) == "waiting_token":
        process_token(msg)

    elif user_state.get(uid) == "waiting_name":
        if uid in saved_tokens:
            set_new_name(msg, saved_tokens[uid])

    else:
        bot.send_message(msg.chat.id, f"{e('👋')} استخدم الأزرار أو /start", reply_markup=main_menu())

# ========== [ معالجة التوكن ] ==========
def process_token(msg):
    uid = msg.from_user.id
    raw = msg.text.strip()
    if ":" not in raw or len(raw) < 35:
        bot.send_message(msg.chat.id, f"{bold('❌ تنسيق خاطئ!')}", reply_markup=main_menu())
        user_state[uid] = None
        return
    loading = bot.send_message(msg.chat.id, f"{e('🔤')} جاري الفحص...")
    res = validate_token(raw)
    bot.delete_message(msg.chat.id, loading.message_id)
    if res["valid"]:
        saved_tokens[uid] = raw
        user_state[uid] = None
        creation = decode_bot_id(res["id"])
        report = (
            f"{e('✅')} {bold('تم بنجاح!')}\n\n"
            f"{bold('🤖 الهدف:')}\n"
            f"• الاسم: {res['first_name']}\n"
            f"• @{res['username']}\n"
            f"• ID: <code>{res['id']}</code>\n"
            f"• تاريخ: {creation}\n\n"
            f"{bold('الصلاحيات:')}\n"
            f"• مجموعات: {'✅' if res['can_join_groups'] else '❌'}\n"
            f"• قراءة: {'✅' if res['can_read_all_group_messages'] else '❌'}\n"
            f"• Inline: {'✅' if res['supports_inline_queries'] else '❌'}\n\n"
            f"{quote('اختر العملية التالية:')}"
        )
        bot.send_message(msg.chat.id, report, reply_markup=arsenal_menu())
    else:
        bot.send_message(msg.chat.id, f"{e('💀')} {bold('فشل!')}\n{res['error']}", reply_markup=main_menu())
        user_state[uid] = None

# ========== [ أزرار الكول باك ] ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = call.from_user.id
    if call.data == "change_photo":
        user_state[uid] = "waiting_photo"
        bot.send_message(call.message.chat.id, f"{bold('📸 أرسل الصورة الجديدة:')}")
        bot.answer_callback_query(call.id)
    elif call.data == "change_name":
        if uid in saved_tokens:
            user_state[uid] = "waiting_name"
            bot.send_message(call.message.chat.id, f"{bold('✏️ أرسل الاسم الجديد:')}")
        bot.answer_callback_query(call.id)
    elif call.data == "recheck_token":
        if uid in saved_tokens:
            res = validate_token(saved_tokens[uid])
            bot.answer_callback_query(call.id, "✅ شغال" if res["valid"] else "❌ مات")
        else:
            bot.answer_callback_query(call.id, "لا توكن")
    elif call.data == "delete_photo":
        if uid in saved_tokens:
            try:
                r = requests.post(f"https://api.telegram.org/bot{saved_tokens[uid]}/deleteMyProfilePhoto", timeout=10)
                bot.answer_callback_query(call.id, "🗑️ تم" if r.json().get("ok") else "❌ فشل")
            except:
                bot.answer_callback_query(call.id, "❌ خطأ")
        else:
            bot.answer_callback_query(call.id, "لا توكن")

# ========== [ استقبال الصورة ] ==========
@bot.message_handler(content_types=['photo'])
def handle_photo(msg):
    uid = msg.from_user.id
    if user_state.get(uid) != "waiting_photo" or uid not in saved_tokens:
        return
    token = saved_tokens[uid]
    try:
        file_info = bot.get_file(msg.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        img = requests.get(file_url).content
        r = requests.post(f"https://api.telegram.org/bot{token}/setMyProfilePhoto",
                          files={"photo": ("photo.jpg", img, "image/jpeg")}, timeout=30)
        bot.send_message(msg.chat.id, "✅ تم تغيير الصورة" if r.json().get("ok") else "❌ فشل", reply_markup=main_menu())
    except Exception as ex:
        bot.send_message(msg.chat.id, f"❌ خطأ: {ex}", reply_markup=main_menu())
    user_state[uid] = None

# ========== [ تغيير الاسم ] ==========
def set_new_name(msg, token):
    name = msg.text.strip()
    if len(name) < 1 or len(name) > 64:
        bot.send_message(msg.chat.id, "❌ 1-64 حرف", reply_markup=main_menu())
        return
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/setMyName", data={"name": name}, timeout=10)
        bot.send_message(msg.chat.id, f"✅ تم تغيير الاسم: {bold(name)}" if r.json().get("ok") else "❌ فشل", reply_markup=main_menu())
    except Exception as ex:
        bot.send_message(msg.chat.id, f"❌ خطأ: {ex}", reply_markup=main_menu())

# ========== [ تشغيل ] ==========
if __name__ == "__main__":
    print(f"🚀 البوت شغال...")
    try:
        bot.infinity_polling()
    except Exception as ex:
        print(f"❌ {ex}")
        time.sleep(5)
        bot.infinity_polling()
