# app.py
from flask import Flask, request, jsonify

app = Flask(__name__)

# تابع کمکی برای استانداردسازی متن فارسی
def normalize_farsi(text):
    if not text:
        return ""
    # تبدیل ی و ک عربی به فارسی، حذف فاصله مجازی و تبدیل به حروف کوچک
    return text.replace('ي', 'ی').replace('ك', 'ک').replace('\u200c', ' ').lower().strip()

# 🧠 منطق NLU محلی مبتنی بر قوانین (Rule-Based NLU)
def get_intent_and_params(message):
    normalized_msg = normalize_farsi(message)
    
    # 1. تشخیص گزارش فروش
    if 'گزارش' in normalized_msg or 'فروش' in normalized_msg or 'سود' in normalized_msg:
        intent = 'sales_report'
        period = ''
        if 'امروز' in normalized_msg or 'روزانه' in normalized_msg:
            period = 'daily'
        elif 'هفتگی' in normalized_msg or 'هفته' in normalized_msg:
            period = 'weekly'
        elif 'ماهانه' in normalized_msg or 'ماه' in normalized_msg:
            period = 'monthly'
        elif 'سالانه' in normalized_msg or 'سال' in normalized_msg:
            period = 'yearly'
        return {'intent': intent, 'period': period if period else 'monthly'}

    # 2. تشخیص قیمت بازار (طلا/دلار)
    if 'قیمت' in normalized_msg and ('دلار' in normalized_msg or 'طلا' in normalized_msg or 'سکه' in normalized_msg):
        intent = 'get_market_price'
        asset = ''
        if 'دلار' in normalized_msg:
            asset = 'دلار'
        elif 'طلا' in normalized_msg or 'سکه' in normalized_msg:
            asset = 'طلا'
        return {'intent': intent, 'asset': asset}

    # 3. تشخیص موجودی و قیمت کالا
    # این منطق باید دقیق‌تر شود، اما برای شروع کار می‌کند.
    if 'قیمت' in normalized_msg and 'چند' in normalized_msg:
        intent = 'get_price'
        # اینجا باید با منطق پیشرفته‌تر، نام کالا را استخراج کنیم.
        # برای سادگی، فرض می‌کنیم کالا بعد از کلمه "قیمت" می‌آید (که بسیار ساده‌سازانه است)
        parts = normalized_msg.split('قیمت')
        item_name = parts[1].split('چند')[0].strip() if len(parts) > 1 else ''
        return {'intent': intent, 'item_name': item_name if item_name else 'نامعلوم'}
        
    if 'موجودی' in normalized_msg:
        intent = 'get_inventory'
        # مشابه بالا
        parts = normalized_msg.split('موجودی')
        item_name = parts[1].strip().split(' ')[0].strip() if len(parts) > 1 else 'نامعلوم'
        return {'intent': intent, 'item_name': item_name}

    # 4. تشخیص چت
    if 'سلام' in normalized_msg or 'چطوری' in normalized_msg or 'هستی' in normalized_msg:
        return {'intent': 'chat', 'text': 'من یک دستیار تحلیل هستم. لطفا سوال خود را در مورد کالاها یا گزارش‌ها بپرسید.'}
        
    # نیت نامشخص
    return {'intent': 'chat', 'text': 'متاسفانه متوجه نشدم. لطفا سوال خود را واضح تر بپرسید.'}


@app.route('/', methods=['POST'])
def handle_nlu_request():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400

        # اجرای منطق تشخیص نیت
        nlu_result = get_intent_and_params(message)

        # برگرداندن JSON نهایی به همان شکلی که انتظار داریم
        return jsonify({
            'ok': True,
            'parsed_json': nlu_result
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # این خط فقط برای اجرای محلی است
    app.run(debug=True, port=8000)