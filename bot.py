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
    return
