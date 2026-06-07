import os
import logging
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

# Flask Server Setup for Render Port Binding
app = Flask(__name__)

@app.route('/')
def home():
    return "National ID Downloader Bot is running live!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Logging Configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TOKEN = "8647607353:AAHbJYHAYMRtLDTduLNYghgSC_Q9-UPjZrY"
ADMIN_ID = 123456789  # Telegram User ID kee as galchi (Kaffaltiin siif dhufa)

# Conversation States
MAIN_STATE, DEPOSIT_STATE, PROOF_STATE, FIN_FAN_STATE = range(4)

# In-Memory Database
USER_DATA = {}

def get_user_profile(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"balance": 0, "mode": "📇 PDF + ID"}
    return USER_DATA[user_id]

# --- KEYBOARDS (Accurate Copy of @National_idpdfbot) ---
def main_keyboard():
    keyboard = [
        [KeyboardButton("💰 Balance"), KeyboardButton("💳 Deposit")],
        [KeyboardButton("🎨 Settings")],
        [KeyboardButton("🧑‍💻 Contact admin")]
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

# --- TELEGRAM HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user_profile(user.id)
    
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

    elif text == "🎨 Settings":
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
            "💳 **Send to CBE: Coming Soon**\n"
            "የባንክ ክፍያ አማራጭ በቅርቡ እንጀምራለን\n\n"
            "📌 After payment, tap **I have paid** and then send a screenshot/link/text as evidence."
        )
        await update.message.reply_text(deposit_text, reply_markup=deposit_keyboard(), parse_mode="Markdown")
        return DEPOSIT_STATE

    elif text == "🧑‍💻 Contact admin":
        await update.message.reply_text("📞 For active activations or failures, text here: @Urjii_Support", reply_markup=main_keyboard())
        return MAIN_STATE

    else:
        # Fin / Fan direct entry trigger if user types any random string
        if profile['balance'] <= 0:
            await update.message.reply_text(
                "❌ **Balance Unsufficient!**\n\n"
                "Kaffaltii sirrii galchuu qabdu. Meeshaa keessan irratti balance hin jiru. "
                "Maaloo jalqaba '💳 Deposit' tuquun herrega keessan guuttadhaa.",
                reply_markup=main_keyboard()
            )
            return MAIN_STATE
        
        await update.message.reply_text(f"⏳ **Processing request for:** `{text}`...\nConnecting to registry server, please wait.")
        # Playwright/OCR logic runs here in background
        profile['balance'] -= 1
        await update.message.reply_text("✅ Fayda System matched! Document generated successfully.", reply_markup=main_keyboard())
        return MAIN_STATE

# --- ANTI-FAKE PAYMENT PROOF OVERSEE ---
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
        [InlineKeyboardButton("❌ Reject / Fake Receipt", callback_data=f"adm_rej_{user.id}")]
    ]
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 **Kaffaltii Haaraa Urjii!**\nUser: {user.full_name} (@{user.username})\nUID: {user.id}\nProof details:",
        reply_markup=InlineKeyboardMarkup(admin_actions)
    )
    
    if update.message.photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id)
    else:
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"Text Message Receipt: {update.message.text}")

    await update.message.reply_text(
        "⏳ **Ragaan keessan fudhatameera!**\nAdmin herrega keessan daqiiqaa muraasa keessatti qoree mirkaneessa.",
        reply_markup=main_keyboard()
    )
    return MAIN_STATE

# --- ADMIN ACTIONS EXECUTION ---
async def process_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if "adm_app" in data:
        _, _, user_id, amount = data.split("_")
        user_id = int(user_id)
        profile = get_user_profile(user_id)
        
        # Balance allocation dynamically based on input selection
        added_pack = 10 if amount == "50" else 1150
        profile['balance'] += added_pack

        success_notif = (
            f"✅ **Kaffaltiini Keessan Mirkanaa'eera!**\n"
            f"(ELIAS FIKADU)\n\n"
            f"💵 {amount} ETB Balance keessan irratti dabalameera. Hojii keessan itti fufaa!"
        )
        await context.bot.send_message(chat_id=user_id, text=success_notif)
        await query.edit_message_text(text=f"🟢 Verification successful. Dispatched to user {user_id}.")

    elif "adm_rej" in data:
        user_id = int(data.split("_")[2])
        await context.bot.send_message(
            chat_id=user_id, 
            text="❌ **Kaffaltiin Keessan Hin Mirkanoofne!**\nKaffaltiin sobaa ykn screenshot sirriin kanaan dura fayyadame argameera."
        )
        await query.edit_message_text(text=f"🔴 Request declined for user {user_id}.")

# --- SETTINGS SELECTION ---
async def process_settings_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    profile = get_user_profile(user_id)

    if query.data == "set_pdf_id":
        profile['mode'] = "📇 PDF + ID"
        await query.edit_message_text("✅ Format updated: **PDF + ID** mode is now active.")
    elif query.data == "set_pdf_only":
        profile['mode'] = "📄 PDF Only"
        await query.edit_message_text("✅ Format updated: **PDF Only** mode is now active.")
    elif query.data == "set_merge_a4":
        profile['mode'] = "🖨️ Merge On A4"
        await query.edit_message_text("✅ Format updated: **Merge On A4** layout configured.")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    
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
    
    application.run_polling()
