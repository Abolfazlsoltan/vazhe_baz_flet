# واژه‌باز | Word Play 🎯

بازی حدس کلمه فارسی با رابط مدرن و موبایل‌پسند، ساخته‌شده با Flet و Python.

## امکانات
- بازی آفلاین با دسته‌بندی‌های فارسی
- شمارش معکوس، امتیاز و راهنمایی محدود
- بازخورد رنگی برای حروف درست و اشتباه
- رابط تیره و واکنش‌گرا
- تنظیم زمان هر دور

## اجرا روی رایانه
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## ساخت APK اندروید
به Python 3.10 تا 3.12 و ابزارهای ساخت Android نیاز دارید. سپس:
```bash
pip install -r requirements.txt
flet build apk
```

برای ساخت اندروید، استفاده از Linux یا WSL پیشنهاد می‌شود. راهنمای رسمی Flet را برای وابستگی‌های Android بررسی کنید.

## وضعیت پروژه
این نسخه یک بازی بومی Flet است، نه اجرای مستقیم HTML در WebView. نسخه فعلی آفلاین است و اتصال هوش مصنوعی آنلاین یا چندنفره ندارد.
