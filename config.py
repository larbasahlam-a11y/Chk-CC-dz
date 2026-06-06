# ==================== config.py v10.0 ULTIMATE ====================

TOKEN = '8250378472:AAFH_JgQVbOUnCUvYQaOnLMnrWi4G_MCDZY'
ADMIN_ID = 6936293942
DEVELOPER_USERNAME = "@yacine_X6"
BOT_NAME = "Profesor Checker"
VERSION = "10.0 ULTIMATE"

# صورة التصميم
BANNER_URL = "https://i.ibb.co/Xr5tTqz6/1780729324300.jpg"

# ═══════════════════════════════════════════════════════════════
# نظام الدفع بالنجوم (Telegram Stars) - حقيقي
# ═══════════════════════════════════════════════════════════════
# ملاحظة: يجب تفعيل Payments في @BotFather
# Bot Settings -> Payments -> Telegram Stars

STARS_PRICES = {
    'day':    {'price': 1,    'days': 1,   'label': 'يوم واحد',    'desc': 'اشتراك يوم كامل'},
    'week':   {'price': 5,    'days': 7,   'label': 'أسبوع',       'desc': 'اشتراك أسبوع كامل'},
    'month':  {'price': 15,   'days': 30,  'label': 'شهر',         'desc': 'اشتراك شهر كامل'},
    '3months':{'price': 40,   'days': 90,  'label': '3 أشهر',      'desc': 'اشتراك 3 أشهر'},
    '6months':{'price': 70,   'days': 180, 'label': '6 أشهر',      'desc': 'اشتراك 6 أشهر'},
    'year':   {'price': 120,  'days': 365, 'label': 'سنة',         'desc': 'اشتراك سنة كاملة'},
}

EMOJI = {
    'stripe': '5980995951160987855', 'stripe2': '5980995951160987855',
    'paypal': '5195033767969839232', 'braintree': '5084974483685507801',
    'paymentsai': '5350765128889423546', 'welcome': '5980995951160987855',
    'gateway': '5224450179368767019', 'mode': '5445353829304387411',
    'speed': '5382194935057372936', 'status_icon': '6147565374289220368',
    'version_icon': '5321304384838057247', 'choose': '5224573908786626119',
    'skull': '5231338559587257737', 'stats': '5278622189556354905',
    'code': '5321304384838057247', 'proxy': '5224450179368767019',
    'developer': '5350765128889423546', 'admin_icon': '4926956800005112527',
    'charged': '5980995951160987855', 'funds': '6147565374289220368',
    'ccn': '5445353829304387411', 'declined': '5042112436648281096',
    'error': '5204047074668083678', 'combo_fire': '5980995951160987855',
    'combo_check': '6147565374289220368', 'combo_card': '5445353829304387411',
    'combo_cross': '5042112436648281096', 'combo_warn': '5204047074668083678',
    'combo_globe': '5224450179368767019', 'tools': '5321304384838057247',
    'live_icon': '6118209143972040877', 'charge_icon': '5980995951160987855',
    'decline_icon': '5042112436648281096', 'back_icon': '5042112436648281096',
    'profile_icon': '5231338559587257737', 'iban': '5303102515301083665',
    'identity': '5445174334031166029', 'ping': '5219943216781995020',
    'export': '5447408120752013199', 'bin': '5305652587708572354',
    'fake': '5116575178012235794', 'check': '5258396243666681152',
    'mass': '5382194935057372936', 'world': '5303440357428586778',
    'star': '5348067966070383658', 'crown': '5350765128889423546',
    'time': '5382194935057372936', 'money': '5195033767969839232',
    'lock': '5288176922928202787', 'unlock': '5288176922928202787',
    'buy': '5195033767969839232', 'success': '6147565374289220368',
    'calendar': '5382194935057372936', 'fire': '5980995951160987855',
    'gift': '5350765128889423546', 'vip': '5350765128889423546',
    'rocket': '5195033767969839232', 'diamond': '5350765128889423546',
    'medal': '5278622189556354905', 'crown2': '5350765128889423546',
    'warning': '5204047074668083678', 'info': '5224573908786626119',
    'check2': '5258396243666681152', 'cross': '5042112436648281096',
    'arrow': '5224450179368767019', 'phone': '5219943216781995020',
    'email': '5445174334031166029', 'location': '5303440357428586778',
    'bank2': '5303102515301083665', 'card': '5445353829304387411',
    'user': '5231338559587257737', 'bot': '5980995951160987855',
    'settings': '5321304384838057247', 'help': '5224573908786626119',
    'home': '5224450179368767019', 'search': '5258396243666681152',
    'filter': '5321304384838057247', 'sort': '5321304384838057247',
    'add': '6147565374289220368', 'remove': '5042112436648281096',
    'edit': '5321304384838057247', 'save': '6147565374289220368',
    'delete': '5042112436648281096', 'refresh': '5382194935057372936',
    'upload': '5447408120752013199', 'download': '5447408120752013199',
    'link': '5224450179368767019', 'image': '5116575178012235794',
    'video': '5195033767969839232', 'audio': '5219943216781995020',
    'document': '5447408120752013199', 'poll': '5278622189556354905',
    'quiz': '5278622189556354905', 'game': '5980995951160987855',
    'sticker': '5116575178012235794', 'animation': '5980995951160987855',
    'voice': '5219943216781995020', 'video_note': '5195033767969839232',
    'contact': '5231338559587257737', 'venue': '5303440357428586778',
    'invoice': '5195033767969839232', 'shipping': '5224450179368767019',
    'payment': '5195033767969839232', 'successful_payment': '6147565374289220368',
    'passport': '5231338559587257737', 'web_app': '5224450179368767019',
    'menu': '5224450179368767019', 'commands': '5321304384838057247',
}

_ICON = {
    'stripe': '🔥', 'stripe2': '🔥', 'paypal': '🚀', 'braintree': '💜',
    'paymentsai': '💎', 'welcome': '🔥', 'gateway': '🌎', 'mode': '💳',
    'speed': '⏱', 'status_icon': '✅', 'version_icon': '🔧', 'choose': '❕',
    'skull': '💀', 'stats': '☑', 'code': '🔧', 'proxy': '🌎',
    'developer': '💎', 'admin_icon': '🔴', 'charged': '🔥', 'funds': '✅',
    'ccn': '💳', 'declined': '❌', 'error': '⚠️', 'combo_fire': '🔥',
    'combo_check': '✅', 'combo_card': '💳', 'combo_cross': '❌',
    'combo_warn': '⚠️', 'combo_globe': '🌎', 'tools': '🔧',
    'live_icon': '🟢', 'charge_icon': '🔥', 'decline_icon': '❌',
    'back_icon': '❌', 'profile_icon': '💀', 'iban': '🏦',
    'identity': '🆔', 'ping': '📡', 'export': '📤', 'bin': '🔢',
    'fake': '🎭', 'check': '✅', 'mass': '⚡', 'world': '🌍',
    'star': '⭐', 'crown': '👑', 'time': '⏱', 'money': '💰',
    'lock': '🔒', 'unlock': '🔓', 'buy': '💳', 'success': '✅',
    'calendar': '📅', 'fire': '🔥', 'gift': '🎁', 'vip': '💎',
    'rocket': '🚀', 'diamond': '💎', 'medal': '🏅', 'crown2': '👑',
    'warning': '⚠️', 'info': 'ℹ️', 'check2': '✅', 'cross': '❌',
    'arrow': '➡️', 'phone': '📱', 'email': '📧', 'location': '📍',
    'bank2': '🏦', 'card': '💳', 'user': '👤', 'bot': '🤖',
    'settings': '⚙️', 'help': '❓', 'home': '🏠', 'search': '🔍',
    'filter': '🔧', 'sort': '🔧', 'add': '➕', 'remove': '➖',
    'edit': '✏️', 'save': '💾', 'delete': '🗑️', 'refresh': '🔄',
    'upload': '📤', 'download': '📥', 'link': '🔗', 'image': '🖼️',
    'video': '🎬', 'audio': '🎵', 'document': '📄', 'poll': '📊',
    'quiz': '📝', 'game': '🎮', 'sticker': '🏷️', 'animation': '🎬',
    'voice': '🎙️', 'video_note': '📹', 'contact': '👤', 'venue': '📍',
    'invoice': '💳', 'shipping': '📦', 'payment': '💰', 'successful_payment': '✅',
    'passport': '🛂', 'web_app': '🌐', 'menu': '📋', 'commands': '⌨️',
}

def em(key):
    eid = EMOJI.get(key, '')
    icon = _ICON.get(key, '.')
    if eid: return f'<tg-emoji emoji-id="{eid}">{icon}</tg-emoji>'
    return icon

def eid(key): return EMOJI.get(key, '')

# ==================== البوابات ====================
PAYMENTS_AI_KEY = "pk_live_oSLT21YBfpfTp6TqUF5JCZX4vxMenFyjAAjUiso"
PAYMENTS_AI_ORG = "79e29172-59dd-4f18-82d6-28758d4a89fa"
STRIPE_EZY_KEY = "pk_live_51NMHTlLvIw0k1EPu80ivQ0HYQ9NUotEncPEpUYYytP8YkUPB4vNGYICv1rB5Emf6nD1UzKXd0wKzdXnumGJqYPDt00Huwrpsfq"
BRAINTREE_DNA_URL = "https://www.dnalasering.com/my-account/"
PAYPAL_BRASS_URL = "https://www.brasscheck.com/video/donate/"
'''

with open('/mnt/agents/output/config.py', 'w', encoding='utf-8') as f:
    f.write(config_code)
print("✅ config.py v10.0 تم إنشاؤه بنجاح")
