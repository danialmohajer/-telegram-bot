# ربات دانیال مهاجر

نسخه اول ربات:
- `/start`
- دکمه شروع ثبت درخواست
- دریافت نام و نام خانوادگی
- دریافت شماره با دکمه Share Contact
- ارسال لید جدید برای مدیر
- لینک کانال دانیال مهاجر
- `/admin` برای ثبت چت مدیر

## اطلاعاتی که از شما می‌گیرد

نام + شماره تلفن

## امنیت

Token ربات داخل کد قرار داده نشده است.
آن را فقط به عنوان Environment Variable با نام `BOT_TOKEN` وارد کنید.

## مدیر

نام کاربری مدیر:
`@hamidi_arsalan`

بعد از راه‌اندازی، خود مدیر یک بار `/admin` را برای ربات بفرستد.

## استقرار روی Render

Render یک متغیر محیطی به نام `RENDER_EXTERNAL_URL` در Web Service ایجاد می‌کند؛ کد از آن برای webhook استفاده می‌کند.

در Render:
1. New → Web Service
2. این پروژه را از GitHub وصل کنید.
3. Build Command:
   `pip install -r requirements.txt`
4. Start Command:
   `python bot.py`
5. Environment Variables:
   - `BOT_TOKEN` = توکن BotFather
   - `ADMIN_USERNAME` = `hamidi_arsalan`
   - `CHANNEL_URL` = `https://t.me/danialmohajerofficial`
   - `WEBHOOK_SECRET` = یک عبارت تصادفی

## تست

بعد از Deploy:
1. با حساب `@hamidi_arsalan` ربات را باز کنید.
2. `/admin` را بفرستید.
3. `/start` را بزنید.
4. با یک حساب دیگر ربات را تست کنید.
5. نام و شماره را ارسال کنید.
6. باید لید برای چت مدیر بیاید.

## نکته مهم برای استفاده تجاری

نسخه اولیه لید را مستقیماً در Telegram به مدیر می‌فرستد و برای سادگی وابسته به Google Sheets یا CRM نیست.

برای نسخه تجاری پایدار، مرحله بعد باید ذخیره دائمی Leadها (مثلاً PostgreSQL/CRM) اضافه شود.
