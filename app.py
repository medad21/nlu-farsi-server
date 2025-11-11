# app.py
from flask import Flask, request, jsonify
import re # برای حذف هوشمند کلمات کلیدی

app = Flask(__name__)

# --- 1. تعریف کلمات کلیدی برای هر نیت ---

# کلمات کلیدی برای تشخیص قیمت کالا
PRICE_KEYWORDS = [
    'قیمت', 'قیم', 'نرخ', 'چنده', 'چند', 'بگو چنده', 'قیمتش چنده'
]
# کلمات کلیدی برای تشخیص موجودی کالا
INVENTORY_KEYWORDS = [
    'موجودی', 'تعداد', 'انبار', 'چند عدد', 'چند تا', 'موجوده', 'داریم'
]
# کلمات کلیدی برای تشخیص گزارش فروش
REPORT_KEYWORDS = [
    'گزارش', 'فروش', 'سود', 'آمار', 'چقدر فروختیم'
]
# کلمات کلیدی برای تشخیص بازار
MARKET_KEYWORDS = [
    'طلا', 'دلار', 'سکه', 'ارز', 'یورو'
]
# کلمات کلیدی برای تشخیص محاوره (چت)
CHAT_KEYWORDS = {
    'سلام': 'سلام! در خدمتم. چه کمکی می‌تونم بکنم؟',
    'چطوری': 'ممنون، آماده‌ام به شما کمک کنم.',
    'خوبی': 'ممنون، آماده‌ام به شما کمک کنم.',
    'صبح بخیر': 'صبح شما هم بخیر! چه روز خوبی برای تحلیل داده‌هاست.',
    'عصر بخیر': 'عصر بخیر! امیدوارم روز خوبی داشته باشید.',
    'شب بخیر': 'شب بخیر!',
    'وقت بخیر': 'وقت شما هم بخیر. بفرمایید.',
    'درود': 'درود بر شما. آماده شنیدن دستورتون هستم.',
    'خداحافظ': 'خداحافظ! روز خوبی داشته باشید.',
    'مرسی': 'خواهش می‌کنم! کار دیگه‌ای بود در خدمتم.',
    'ممنون': 'خواهش می‌کنم! کار دیگه‌ای بود در خدمتم.',
    'تشکر': 'خواهش می‌کنم! کار دیگه‌ای بود در خدمتم.'
}

# کلمات کلیدی عمومی که باید از نام کالا حذف شوند
GENERAL_STOP_WORDS = [
    'لطفا', 'بگو', 'رو', 'بهم', 'به من', 'رو بگو', 'را', 'لطفا بگو'
]

# --- 2. توابع کمکی ---

def normalize_farsi(text):
    """استانداردسازی و تمیز کردن متن فارسی."""
    if not text:
        return ""
    text = text.replace('ي', 'ی').replace('ك', 'ک').replace('\u200c', ' ')
    text = text.lower().strip()
    return text

def remove_keywords(text, keywords):
    """
    از یک متن، تمام کلمات کلیدی موجود در لیست را حذف می‌کند.
    این تابع برای استخراج نام کالا استفاده می‌شود.
    """
    # ایجاد یک الگوی regex برای یافتن تمام کلمات کلیدی
    # \b ensures we match whole words
    pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
    # جایگزینی کلمات کلیدی با رشته خالی
    cleaned_text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    # حذف فاصله‌های اضافی که ممکن است ایجاد شده باشد
    return ' '.join(cleaned_text.split())


# --- 3. مغز اصلی NLU ---

def get_intent_and_params(message):
    normalized_msg = normalize_farsi(message)
    
    # --- اولویت اول: نیت‌های خاص (بازار و گزارش) ---
    
    # 1. تشخیص قیمت بازار (طلا/دلار)
    if any(kw in normalized_msg for kw in MARKET_KEYWORDS):
        intent = 'get_market_price'
        asset = 'طلا'
        if 'دلار' in normalized_msg or 'یورو' in normalized_msg or 'ارز' in normalized_msg:
            asset = 'دلار'
        elif 'سکه' in normalized_msg:
            asset = 'طلا' # فرض می‌کنیم منظور همان طلاست
        return {'intent': intent, 'asset': asset}

    # 2. تشخیص گزارش فروش
    if any(kw in normalized_msg for kw in REPORT_KEYWORDS):
        intent = 'sales_report'
        period = 'monthly' # پیش فرض ماهانه
        if 'امروز' in normalized_msg or 'روزانه' in normalized_msg:
            period = 'daily'
        elif 'هفتگی' in normalized_msg or 'هفته' in normalized_msg:
            period = 'weekly'
        elif 'سالانه' in normalized_msg or 'سال' in normalized_msg:
            period = 'yearly'
        return {'intent': intent, 'period': period}

    # --- اولویت دوم: نیت‌های کالا (قیمت و موجودی) ---
    
    # 3. تشخیص قیمت کالا
    if any(kw in normalized_msg for kw in PRICE_KEYWORDS):
        intent = 'get_price'
        # استخراج نام کالا: حذف تمام کلمات کلیدی قیمت و کلمات عمومی
        all_stopwords = PRICE_KEYWORDS + GENERAL_STOP_WORDS
        item_name = remove_keywords(normalized_msg, all_stopwords)
        return {'intent': intent, 'item_name': item_name or 'نامشخص'}

    # 4. تشخیص موجودی کالا
    if any(kw in normalized_msg for kw in INVENTORY_KEYWORDS):
        intent = 'get_inventory'
        # استخراج نام کالا: حذف تمام کلمات کلیدی موجودی و کلمات عمومی
        all_stopwords = INVENTORY_KEYWORDS + GENERAL_STOP_WORDS
        item_name = remove_keywords(normalized_msg, all_stopwords)
        return {'intent': intent, 'item_name': item_name or 'نامشخص'}

    # --- اولویت آخر: چت و محاوره ---
    for chat_kw, response in CHAT_KEYWORDS.items():
        if chat_kw in normalized_msg:
            return {'intent': 'chat', 'text': response}
            
    # نیت نامشخص
    return {'intent': 'chat', 'text': 'متاسفانه متوجه نشدم. لطفا سوال خود را واضح تر بپرسید.'}


# --- 4. راه‌اندازی سرور Flask ---

@app.route('/', methods=['POST'])
def handle_nlu_request():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400

        # اجرای منطق تشخیص نیت
        nlu_result = get_intent_and_params(message)

        # برگرداندن JSON نهایی
        return jsonify({
            'ok': True,
            'parsed_json': nlu_result
        })

    except Exception as e:
        app.logger.error(f"Error processing request: {e}")
        return jsonify({'error': str(e)}), 500

# این خط برای اجرای gunicorn در Railway لازم نیست، اما برای تست محلی خوب است
if __name__ == '__main__':
    app.run(debug=True, port=8000)
