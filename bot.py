import os
import asyncio
import logging
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Flask setup (Render akka port irratti bot-in akka hin dhaabbanne godha)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running live!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Token
TOKEN = "8647607353:AAHbJYHAYMRtLDTduLNYghgSC_Q9-UPjZrY"

# Conversation states
MAIN_MENU = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("💰 Balance"), KeyboardButton("💳 Deposit")],
        [KeyboardButton("⚙️ Settings"), KeyboardButton("📞 Contact admin")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Welcome! Select an option:", reply_markup=reply_markup)
    return MAIN_MENU

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "💰 Balance":
        await update.message.reply_text("Your balance is 0 ETB.")
    elif text == "💳 Deposit":
        await update.message.reply_text("Follow the instructions to deposit.")
    return MAIN_MENU

if __name__ == '__main__':
    # Flask thread jalqabsiisi
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Telegram Bot jalqabsiisi - LINE 142 kan sirrate
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Conversation Handler - LINE 308 kan sirrate
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    application.add_handler(conv_handler)
    application.run_polling()
