import os
import logging
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

# Flask Server for Render Port Binding
app = Flask(__name__)

@app.route('/')
def home():
    return "National ID Bot is running live!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Logging Configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Settings & Admin ID (Bakka kanaan ID kee galchi)
TOKEN = "8647607353:AAHbJYHAYMRtLDTduLNYghgSC_Q9-UPjZrY"
ADMIN_ID = 123456789  # Telegram User ID kee as galchi (Kaffaltiin siif dhiyaata)

# Conversation States
MAIN_STATE, DEPOSIT_STATE, PROOF_STATE, FIN_FAN_STATE = range(4)

# User Database Mockup (Kaffaltii qorachuuf)
USER_DATA = {}

def get_user_profile(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"balance": 0, "mode": "PDF + ID"}
    return USER_DATA[user_id]

# --- KEYBOARDS ---
def main_keyboard():
    keyboard = [
        [KeyboardButton("🔑 Send FAN / FIN")],
        [KeyboardButton("⚙️ Settings"), KeyboardButton("💰 Balance")],
        [KeyboardButton("💳 Deposit"), KeyboardButton("📞 Help")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def settings_keyboard():
    keyboard = [
        [InlineKeyboardButton("📇 PDF + ID", callback_data="mode_pdf_id")],
        [InlineKeyboardButton("📄 PDF Only", callback_data="mode_pdf_only")],
        [InlineKeyboardButton("🖨️ Merge On A4", callback_data="mode_merge_a4")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user_profile(user.id)
    
    welcome_text = (
        "🚀 **የአገልግሎታችን መሻሻል መግለጫ / Our service has been improved even further.**\n\n"
        "👋 Welcome! አሁን FIN ወይም FAN/FCN በመላክ ኦሪጅናል የፋይዳ PDF ማግኘት ብቻ ሳይሆን "
        "በጣም በተመጣጣኝ ዋጋ ማግኘት ይችላሉ።\n\n"
        "You can now send your FIN or FAN/FCN to get your original Fayda PDF. "
        "Select an option below to start:"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_keyboard(), parse_mode="Markdown")
    return MAIN_STATE

async def handle_menu_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)

    if text == "💰 Balance":
        msg = (
            f"💰 **Balance Information**\n\n"
            f"▫️ Available Balance: {profile['balance']} PDF Pack\n"
            f"▫️ Current Mode: {profile['mode']}"
        )
        await update.message.reply_text(msg, reply_markup=main_keyboard(), parse_mode="Markdown")
        return MAIN_STATE

    elif text == "⚙️ Settings":
        msg = (
            "⚙️ **Settings Menu / ማስተካከያ**\n\n"
            "Choose your output print format below:"
        )
        await update.message.reply_text(msg, reply_markup=settings_keyboard(), parse_mode="Markdown")
        return MAIN_STATE

    elif text == "💳 Deposit":
        deposit_text = (
            "⬇️ **Select a top-up amount below / የገንዘብ መጠን ይምረጡ:**\n\n"
            "▫️ 5 Pdf = 75 ETB\n"
            "▫️ 10 Pdf = 150 ETB\n"
            "▫️ 20 Pdf = 300 ETB\n"
            "▫️ 30 Pdf = 450 ETB\n"
            "▫️ 50 Pdf = 750 ETB\n"
            "▫️ 100 Pdf = 1500 ETB\n\n"
            "💳 **Bank: CBE (Commercial Bank of Ethiopia)**\n"
            "📌 After payment, tap **'✅ I have paid'** and send text/screenshot as evidence."
        )
        keyboard = [
            [KeyboardButton("✅ I have paid")],
            [KeyboardButton("⬅️ Back")]
        ]
        await update.message.reply_text(deposit_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True), parse_mode="Markdown")
        return DEPOSIT_STATE

    elif text == "🔑 Send FAN / FIN":
        if profile['balance'] <= 0:
            await update.message.reply_text("❌ **Balance-iin keessan qaaniidha!** Please deposit first to use this service.")
            return MAIN_STATE
        await update.message.reply_text("📥 Please enter your **FIN** or **FAN/FCN** Number:")
        return FIN_FAN_STATE

    elif text == "📞 Help":
        await update.message.reply_text("📞 For support or manual inquiries, contact: @Urjii_Support")
        return MAIN_STATE

    return MAIN_STATE

# --- DEPOSIT & ANTI-FAKE PAYMENT SYSTEM ---
async def handle_deposit_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "✅ I have paid":
        await update.message.reply_text("📸 Please send your **Screenshot / Transaction reference text** as evidence:")
        return PROOF_STATE
    else:
        await update.message.reply_text("Returning to main menu...", reply_markup=main_keyboard())
        return MAIN_STATE

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Admin kaffaltii qoratuuf erguu
    admin_keyboard = [
        [InlineKeyboardButton("✅ Approve 50 ETB", callback_data=f"pay_approve_{user.id}_50")],
        [InlineKeyboardButton("✅ Approve 15000 ETB", callback_data=f"pay_approve_{user.id}_15000")],
        [InlineKeyboardButton("❌ Reject / Fake", callback_data=f"pay_reject_{user.id}")]
    ]
    
    # Admine-if gabaasa dhiibuu
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 **New Payment Request!**\nFrom: {user.full_name} (@{user.username})\nID: {user.id}\nCheck the proof below:",
        reply_markup=InlineKeyboardMarkup(admin_keyboard)
    )
    
    # Yoo fakkii (photo) ta'e gara admin-itti dabarsuu
    if update.message.photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id)
    else:
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"Proof Text: {update.message.text}")

    await update.message.reply_text(
        "⏳ **Kaffaltiin Keessan Qoratamaa Jira!**\nYour payment evidence has been submitted to Admin. It will be verified shortly.",
        reply_markup=main_keyboard()
    )
    return MAIN_STATE

# Admin Callback Handler (Approve / Reject)
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if "pay_approve" in data:
        _, _, user_id, amount = data.split("_")
        user_id = int(user_id)
        
        profile = get_user_profile(user_id)
        profile['balance'] += 10 # PDF balance dabaluu (Fkn: 10 pack)
        
        # User-if beksisuu (Akkuma suuraa irratti argamutti)
        success_msg = (
            f"✅ **Kaffaltiini Keessan Mirkanaa'eera!**\n"
            f"(ELIAS FIKADU)\n\n"
            f"💵 {amount} ETB Balance keessan irratti dabalameera. Hojii keessan itti fufaa!"
        )
        await context.bot.send_message(chat_id=user_id, text=success_msg)
        await query.edit_message_text(text=f"🟢 User {user_id} Approved with {amount} ETB successfully.")

    elif "pay_reject" in data:
        user_id = int(data.split("_")[2])
        await context.bot.send_message(chat_id=user_id, text="❌ **Kaffaltiin Keessan Hin Mirkanoofne!** Invalid or Fake transaction proof detected.")
        await query.edit_message_text(text=f"🔴 User {user_id} Request Rejected (Fake/Invalid).")

# --- FIN/FAN HANDLING ---
async def handle_fin_fan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_text = update.message.text
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)
    
    if profile['balance'] <= 0:
        await update.message.reply_text("❌ Error: Balance insufficient.", reply_markup=main_keyboard())
        return MAIN_STATE

    await update.message.reply_text(f"⏳ **Processing your Fayda ID for:** `{input_text}`...\nConnecting to National Registry system...")
    
    # --- AS IRRATTII CODE BACKEND FIN/FAN PLAYWRIGHT SANA GALCHITA ---
    # Fakkeenyaaf, erga xumuramee booda balance hir'isna:
    profile['balance'] -= 1
    
    await update.message.reply_text("✅ **Your Original Fayda PDF is Ready!** Sending document...", reply_markup=main_keyboard())
    return MAIN_STATE

# --- SETTINGS CALLBACK ---
async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    profile = get_user_profile(user_id)

    if query.data == "mode_pdf_id":
        profile['mode'] = "PDF + ID"
        await query.edit_message_text("🔄 Mode changed to: **PDF + ID** (Both PDF and ID card side-by-side)")
    elif query.data == "mode_pdf_only":
        profile['mode'] = "PDF Only"
        await query.edit_message_text("🔄 Mode changed to: **PDF Only** (Original Full Sheet)")
    elif query.data == "mode_merge_a4":
        profile['mode'] = "Merge On A4"
        await query.edit_message_text("🔄 Mode changed to: **Merge On A4** (Multiple IDs tiled together)")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_options)],
            DEPOSIT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deposit_state)],
            PROOF_STATE: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_payment_proof)],
            FIN_FAN_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fin_fan)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^mode_"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^pay_"))
    
    application.run_polling()
