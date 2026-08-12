import os
import re
import logging
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"].strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "hamidi_arsalan").lstrip("@").lower()
CHANNEL_URL = os.getenv(
    "CHANNEL_URL",
    "https://t.me/danialmohajerofficial",
)
PORT = int(os.getenv("PORT", "10000"))

# Render provides this automatically for Web Services.
PUBLIC_URL = (
    os.getenv("PUBLIC_URL", "").rstrip("/")
    or os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
)

# Secret path used for Telegram's webhook URL.
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "danial-mohajer-bot").strip("/")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("danial_mohajer_bot")

# In-memory state is deliberately minimal for this first version.
# The final lead is sent to the admin's Telegram chat, so no CRM/database
# credentials are required in this version.


def is_admin(user) -> bool:
    return bool(
        user
        and user.username
        and user.username.lower() == ADMIN_USERNAME
    )


def start_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📲 شروع ثبت درخواست",
                    callback_data="lead_start",
                )
            ],
            [
                InlineKeyboardButton(
                    "📢 کانال دانیال مهاجر",
                    url=CHANNEL_URL,
                )
            ],
        ]
    )


def phone_keyboard():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton(
                    "📱 ارسال شماره تلفن",
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def normalize_phone(phone: str) -> str:
    # Keep digits and a leading + only.
    phone = phone.strip()
    phone = re.sub(r"[^\d+]", "", phone)

    # Normalize common Iranian forms.
    if phone.startswith("0098"):
        phone = "+98" + phone[4:]
    elif phone.startswith("98") and len(phone) >= 12:
        phone = "+" + phone
    elif phone.startswith("09") and len(phone) == 11:
        phone = "+98" + phone[1:]

    return phone


def looks_like_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone)
    return 10 <= len(digits) <= 15


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user):
        context.application.bot_data["admin_chat_id"] = update.effective_chat.id

    context.user_data.clear()

    await update.message.reply_text(
        "👋 به ربات دانیال مهاجر خوش آمدید.\n\n"
        "برای دریافت مشاوره اولیه، روی «شروع ثبت درخواست» بزنید.",
        reply_markup=start_keyboard(),
    )


async def begin_lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()
    context.user_data["collecting_name"] = True

    await query.message.reply_text(
        "لطفاً نام و نام خانوادگی خود را وارد کنید:"
    )


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("collecting_name"):
        return

    name = (update.message.text or "").strip()

    if len(name) < 2:
        await update.message.reply_text(
            "لطفاً نام و نام خانوادگی خود را وارد کنید."
        )
        return

    context.user_data["name"] = name
    context.user_data["collecting_name"] = False
    context.user_data["collecting_phone"] = True

    await update.message.reply_text(
        "حالا شماره تلفن خود را با دکمه زیر ارسال کنید:",
        reply_markup=phone_keyboard(),
    )


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("collecting_phone"):
        return

    contact = update.message.contact

    if not contact:
        await update.message.reply_text(
            "لطفاً از دکمه «📱 ارسال شماره تلفن» استفاده کنید."
        )
        return

    # Only accept the contact belonging to the person using the bot.
    if contact.user_id and contact.user_id != update.effective_user.id:
        await update.message.reply_text(
            "لطفاً شماره تلفن خودتان را ارسال کنید."
        )
        return

    name = context.user_data.get("name", "").strip()
    phone = normalize_phone(contact.phone_number)
    user = update.effective_user

    admin_chat_id = context.application.bot_data.get("admin_chat_id")

    lead_text = (
        "🔔 لید جدید دانیال مهاجر\n\n"
        f"👤 نام: {name}\n"
        f"📱 تلفن: {phone}\n"
        f"🔗 تلگرام: @{user.username if user.username else 'ندارد'}\n"
        f"🆔 Telegram ID: {user.id}\n"
        f"🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    if admin_chat_id:
        try:
            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=lead_text,
            )
        except Exception:
            logger.exception("Could not send lead to admin.")

    else:
        logger.warning(
            "No admin chat is registered. Ask @%s to send /admin to the bot.",
            ADMIN_USERNAME,
        )

    await update.message.reply_text(
        "✅ اطلاعات شما ثبت شد.\n\n"
        "کارشناسان دانیال مهاجر برای پیگیری درخواست شما با شما تماس خواهند گرفت.",
        reply_markup=ReplyKeyboardRemove(),
    )

    context.user_data.clear()


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user):
        await update.message.reply_text(
            "این دستور برای مدیر ربات فعال نیست."
        )
        return

    context.application.bot_data["admin_chat_id"] = update.effective_chat.id

    await update.message.reply_text(
        "✅ ربات به این چت متصل شد.\n"
        "از این به بعد لیدهای جدید همین‌جا برای شما ارسال می‌شوند."
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "درخواست لغو شد.",
        reply_markup=ReplyKeyboardRemove(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "برای شروع، /start را بزنید."
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled bot error", exc_info=context.error)


def build_app():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(
        __import__("telegram.ext", fromlist=["CallbackQueryHandler"])
        .CallbackQueryHandler(begin_lead, pattern="^lead_start$")
    )

    # Name stage.
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_name,
        )
    )

    # Contact stage.
    app.add_handler(
        MessageHandler(
            filters.CONTACT,
            receive_phone,
        )
    )

    app.add_error_handler(error_handler)
    return app


def main():
    app = build_app()

    if PUBLIC_URL:
        webhook_url = f"{PUBLIC_URL}/telegram/{WEBHOOK_SECRET}"
        logger.info("Starting Telegram webhook on %s", webhook_url)

        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=f"telegram/{WEBHOOK_SECRET}",
            webhook_url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        # Local/VPS fallback. No public URL is needed.
        logger.info("Starting Telegram long polling.")
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )


if __name__ == "__main__":
    main()
