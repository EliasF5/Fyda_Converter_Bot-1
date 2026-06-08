import os
import logging
import threading
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

# Logging Setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TOKEN = "8647607353:AAHbJYHAYMRtLDTduLNYghgSC_Q9-UPjZrY"
ADMIN_ID = 5143360431  # Telegram User ID kee

# States for Conversation
MAIN_STATE, DEPOSIT_STATE, PROOF_STATE = range(3)

# User session memory
USER_DATA = {}

def get_user_profile(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"balance": 0, "mode": "📇 PDF + ID"}
    return USER_DATA[user_id]

# --- KEYBOARDS ---
def main_keyboard():
    keyboard = [
        [KeyboardButton("🔑 Send FAN / FIN")],
        [KeyboardButton("💰 Balance"), KeyboardButton("💳 Deposit")],
        [KeyboardButton("⚙️ Settings"), KeyboardButton("📞 Help")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def settings_keyboard():
    keyboard = [
        [InlineKeyboardButton("📇 PDF + ID — send both PDF and ID together", callback_data="set_pdf_id")],
        [InlineKeyboardButton("📄 PDF Only — download only your original PDF", callback_data="set_pdf_only")],
        [InlineKeyboardButton("🖨️ Merge On A4 — convert multiple to A4", callback_data="set_merge_a4")]
    ]
    return InlineKeyboardMarkup(keyboard)

def deposit_keyboard():
    keyboard = [
        [KeyboardButton("✅ I have paid")],
        [KeyboardButton("⬅️ Back")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- BOT LOGIC HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user_profile(user_id)
    
    welcome_text = (
        "🚀 **አገልግሎታችን በበለጠ ተሻሽሏል፡፡**\n"
        "**Our service has been improved even further.**\n\n"
        "✅ አሁን **FIN** ወይም **FAN/FCN** በመላክ ኦሪጅናል የፋይዳ PDFዎን ማግኘት ብቻ ሳይሆን "
        "ከፈለጉ **PDF + ID** አገልግሎቱንም በአንድ ላይ በጣም በተመጣጣኝ ዋጋ ማግኘት ይችላሉ፡፡\n\n"
        "✅ You can now send your **FIN** or **AN/FCN** not only to receive your original Fayda PDF, "
        "but also, if you choose, to get the **PDF + ID** service together at a very affordable price.\n\n"
        "👇 🔀 All of these options can be adjusted in **Settings** or start checking lower menu:"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_keyboard(), parse_mode="Markdown")
    return MAIN_STATE

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)

    if text == "💰 Balance":
        balance_msg = (
            f"💰 **የአካውንትዎ መረጃ / Balance Information**\n\n"
            f"▫️ Available Balance: `{profile['balance']} PDF Pack`\n"
            f"▫️ Active Mode: `{profile['mode']}`\n\n"
            f"ℹ️ PDF download gochuuf yoo balance hin qabne ta'e '💳 Deposit' tuqi."
        )
        await update.message.reply_text(balance_msg, reply_markup=main_keyboard(), parse_mode="Markdown")
        return MAIN_STATE

    elif text == "⚙️ Settings":
        settings_msg = (
            "⚙️ **Settings Menu / ማስተካከያ**\n\n"
            "Choose your package format below / የፊልም ፎርማት ይምረጡ:"
        )
        await update.message.reply_text(settings_msg, reply_markup=settings_keyboard(), parse_mode="Markdown")
        return MAIN_STATE

    elif text == "💳 Deposit":
        deposit_text = (
            "🔻 **Select a top-up amount bellow / የገንዘብ መጠን ይምረጡ:** 👇\n\n"
            "▫️ 5 Pdf = 75 ETB\n"
            "▫️ 10 Pdf = 150 ETB\n"
            "▫️ 20 Pdf = 300 ETB\n"
            "▫️ 30 Pdf = 450 ETB\n"
            "▫️ 50 Pdf = 750 ETB\n"
            "▫️ 100 Pdf = 1500 ETB\n"
            "🚀 200 + free 15 Pdf = 3000 ETB\n"
            "⭐ 300 + free 30 Pdf = 4500 ETB\n"
            "💎 500 + free 60 Pdf = 7500 ETB\n"
            "👑 1000 + free 150 Pdf = 15000 ETB\n\n"
            "💳 **Send via Telebirr:** `0913701367`\n"
            "👤 **Name:** URJII (ELIAS FIKADU)\n\n"
            "📌 tuqaa, sana booda screenshot ykn koodii kaffaltii ergaa."
        )
        await update.message.reply_text(deposit_text, reply_markup=deposit_keyboard(), parse_mode="Markdown")
        return DEPOSIT_STATE

    elif text == "📞 Help":
        await update.message.reply_text("📞 For active activations or failures, text here: @Urjii_Support", reply_markup=main_keyboard())
        return MAIN_STATE

    else:
        # User yoo FIN/FAN tuqe ykn bareessee erge channel akka seenu gaafata
        join_msg = (
            f"🚀 **To use this bot, you must join our channel:** https://t.me/A_ToolsX"
        )
        await update.message.reply_text(join_msg, reply_markup=main_keyboard(), disable_web_page_preview=False)
        return MAIN_STATE

async def handle_deposit_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "✅ I have paid":
        await update.message.reply_text("📸 Maaloo ragaa kaffaltii keessanii (Screenshot ykn Text) as irratti ergaa:")
        return PROOF_STATE
    else:
        await update.message.reply_text("Returning to menu...", reply_markup=main_keyboard())
        return MAIN_STATE

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    admin_actions = [
        [InlineKeyboardButton("✅ Approve 50 ETB", callback_data=f"adm_app_{user.id}_50")],
        [InlineKeyboardButton("✅ Approve 15000 ETB", callback_data=f"adm_app_{user.id}_15000")],
        [InlineKeyboardButton("❌ Reject / Fake", callback_data=f"adm_rej_{user.id}")]
    ]
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 **Kaffaltii Haaraa!**\nFrom: {user.full_name} (@{user.username})\nUID: {user.id}",
            reply_markup=InlineKeyboardMarkup(admin_actions)
        )
        if update.message.photo:
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id)
        else:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"Receipt Text: {update.message.text}")
    except Exception as e:
        logger.error(f"Admin notification failure: {e}")

    await update.message.reply_text(
        "⏳ **Ragaan keessan fudhatameera!**\nAdmin herrega keessan daqiiqaa muraasa keessatti qoree mirkaneessa.",
        reply_markup=main_keyboard()
    )
    return MAIN_STATE

async def process_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if "adm_app" in data:
        _, _, user_id, amount = data.split("_")
        user_id = int(user_id)
        
        # Balance irratti dabaluu (hamma kaffalame pack gochuuf herregama)
        profile = get_user_profile(user_id)
        profile['balance'] += 10  # Fakkeenyaaf pack herregaa dabalama

        success_notif = (
            f"✅ **Kaffaltiini Keessan Mirkanaa'eera!**\n"
            f"(ELIAS FIKADU)\n\n"
            f"💵 {amount} ETB Balance keessan irratti dabalameera. Hojii keessan itti fufaa!"
        )
        try:
            await context.bot.send_message(chat_id=user_id, text=success_notif)
        except Exception as e:
            logger.error(f"User alert error: {e}")
        await query.edit_message_text(text=f"🟢 User {user_id} approved with {amount} ETB.")

    elif "adm_rej" in data:
        user_id = int(data.split("_")[2])
        try:
            await context.bot.send_message(chat_id=user_id, text="❌ **Kaffaltiin Keessan Hin Mirkanoofne!**\nKaffaltii sobaa ykn screenshot sirriin kanaan dura fayyadame argameera.")
        except Exception as e:
            logger.error(f"User alert error: {e}")
        await query.edit_message_text(text=f"🔴 Request declined.")

async def process_settings_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    profile = get_user_profile(user_id)

    if query.data == "set_pdf_id":
        profile['mode'] = "📇 PDF + ID"
        await query.edit_message_text("✅ Format updated: **PDF + ID** mode active.")
    elif query.data == "set_pdf_only":
        profile['mode'] = "📄 PDF Only"
        await query.edit_message_text("✅ Format updated: **PDF Only** mode active.")
    elif query.data == "set_merge_a4":
        profile['mode'] = "🖨️ Merge On A4"
        await query.edit_message_text("✅ Format updated: **Merge On A4** configured.")

# --- FLASK WEB SERVER FOR WEBHOOK ---
flask_app = Flask(__name__)
application = None

@flask_app.route('/', methods=['GET'])
def index():
    return "Bot is running perfectly!"

@flask_app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if application:
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put_nowait(update)
    return 'OK', 200

def run_bot():
    global application
    application = ApplicationBuilder().token(TOKEN).updater(None).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
            DEPOSIT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deposit_flow)],
            PROOF_STATE: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_payment_proof)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(process_settings_callbacks, pattern="^set_"))
    application.add_handler(CallbackQueryHandler(process_admin_callbacks, pattern="^adm_"))
    
    application.initialize()
    
    render_url = os.environ.get('RENDER_EXTERNAL_URL')
    if render_url:
        application.bot.set_webhook(url=f"{render_url}/{TOKEN}")
        logger.info(f"Webhook connected to: {render_url}")
    
    application.start()

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port)
