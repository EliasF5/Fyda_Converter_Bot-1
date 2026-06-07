import os
import asyncio
import logging
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Flask Web Server Setup (Render akka hin dhabamne port qabata)
app = Flask(__name__)

@app.route('/')
def home():
    return "Fyda Converter Bot is running live!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Logging setup for monitoring
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TOKEN = "8647607353:AAHbJYHAYMRtLDTduLNYghgSC_Q9-UPjZrY"

# Conversation State definitions
MAIN_MENU = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot jalqabsiisuu fi keyboard menu fiduu"""
    keyboard = [
        [KeyboardButton("💰 Balance"), KeyboardButton("💳 Deposit")],
        [KeyboardButton("⚙️ Settings"), KeyboardButton("📞 Contact admin")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋🤖 Welcome to National ID Fayda PDF Downloader Bot!\n\n"
        "Send FIN or FAN/FCN to get your original Fayda PDF in seconds.",
        reply_markup=reply_markup
    )
    return MAIN_MENU

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu cuqaasamu ykn FIN/FAN yommuu ergu kan itti aanu itti fufu"""
    text = update.message.text
    
    if text == "💰 Balance":
        await update.message.reply_text("📉 Your balance is: 0 PDF Pack. Please deposit to top-up.")
    elif text == "💳 Deposit":
        await update.message.reply_text(
            "💳 **Top-up Amount Packages:**\n\n"
            "▫️ 5 Pdf = 75 ETB\n"
            "▫️ 10 Pdf = 150 ETB\n"
            "▫️ 20 Pdf = 300 ETB\n"
            "▫️ 30 Pdf = 450 ETB\n"
            "▫️ 50 Pdf = 750 ETB\n\n"
            "Send payment via Bank and tap 'I have paid' button."
        )
    elif text == "⚙️ Settings":
        await update.message.reply_text("⚙️ **Settings Menu:** Choose modes like PDF+ID, PDF Only, or Merge On A4.")
    elif text == "📞 Contact admin":
        await update.message.reply_text("📞 For support or manual validation, contact: @Urjii_Support")
    else:
        # Bakka FIN/FAN itti processed ta'u (Playwright backend keessatti waamama)
        await update.message.reply_text(f"⏳ Processing your request for: '{text}'... Please wait.")
        
    return MAIN_MENU

if __name__ == '__main__':
    # Flask thread jalqabsiisi (Background irratti akka port bind ta'uuf)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Telegram Application config
    application = ApplicationBuilder().token(TOKEN).build()
    
    # State management handler guutuu
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    application.add_handler(conv_handler)
    
    logger.info("Bot is starting polling mode...")
    application.run_polling()
