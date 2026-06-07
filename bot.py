import os
import asyncio
import logging
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor  

# Flask Server for Render hosting - RAKKINA PORT SANA KAN FURU KANA!
flask_app = Flask('')

@flask_app.route('/')
def home(): 
    return "Bot is running live!"

def run_flask():
    # Yoo variable-ni PORT jedhu Render irraa dhabame, herrega ofumaan 8080 godhata
    port_env = os.environ.get('PORT')
    port = int(port_env) if port_env else 8080
    flask_app.run(host='0.0.0.0', port=port)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8647607353:AAHbJYHAYMRtLDTduLNYghgSC_Q9-UPjZrY"
ADMIN_ID = 6384218679  # ID Telegram kee kan kaffaltiin irratti ergamu

MAIN_MENU, GET_FAN, GET_OTP, GET_DEPOSIT = range(4)
user_data = {}

def get_user_profile(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 0,  
            "output_mode": "PDF + ID",
            "photo_mode": "Grey",
            "template": "Template A",
            "oval_cut": "Off",
            "quality": "High",
            "merge_a4": "Off",
            "session": {}
        }
    return user_data[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    get_user_profile(user_id)
    
    welcome_text = (
        "👋 **Welcome to National ID PDF Bot!**\n\n"
        "ℹ️ **ኦሪጅናል የፋይዳ ፒዲኤፍ ለማግኘት / Fayda PDF:**\n"
        "FIN (ባለ 12 ዲጂት) ወይም FCN/FAN (ባለ 16 ዲጂት) ይላኩ::\n"
        "ከዛም በተመዘገቡበት ስልክ OTP ይደርሶታል፤ OTP እዚህ ሲልኩ ፒዲኤፍ ይደርስዎታል::\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💰 **የአካውንት መሙያ መመሪያ (Telebirr):**\n"
        "📱 **Telebirr Number:** `0913701367`\n"
        "👤 **Account Name:** ELIAS FIKADU\n\n"
        "Kaffaltii erga raawwattanii booda **Transaction ID** ykn **Screenshot** ergaa."
    )
    
    keyboard = [
        [KeyboardButton("🔑 Send FAN / FIN / FIN ቁጥር")],
        [KeyboardButton("⚙️ Settings / ማስተካከያ"), KeyboardButton("💰 Balance / ሂሳብ")],
        [KeyboardButton("💳 Deposit / ብር መሙያ"), KeyboardButton("📞 Help / እርዳታ")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    return MAIN_MENU

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    
    settings_text = (
        f"⚙️ **Bot Output Settings / ማስተካከያ:**\n\n"
        f"▪️ Output Format: `{prof['output_mode']}`\n"
        f"▪️ Photo Mode: `{prof['photo_mode']}`\n"
        f"▪️ Template: `{prof['template']}`\n"
        f"▪️ Quality: `{prof['quality']}`\n\n"
        f"💵 Prices: PDF Only = 15 ETB | PDF + ID = 35 ETB"
    )
    
    keyboard = [
        [InlineKeyboardButton("PDF Only", callback_data="toggle_out_pdf"), InlineKeyboardButton("PDF + ID ID", callback_data="toggle_out_both")],
        [InlineKeyboardButton("Color Photo", callback_data="toggle_photo_color"), InlineKeyboardButton("Grey Photo", callback_data="toggle_photo_grey")],
        [InlineKeyboardButton("❌ Close / ዝጋ", callback_data="menu_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode="Markdown")
    return MAIN_MENU

async def handle_menu_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    
    if "Settings" in text or "ማስተካከያ" in text:
        await show_settings(update, context)
        return MAIN_MENU
    elif "Balance" in text or "የሂሳብ" in text or "💰" in text:
        await update.message.reply_text(f"💵 **Your Balance / የርስዎ ሂሳብ:** {prof['balance']} ETB", parse_mode="Markdown")
        return MAIN_MENU
    elif "Deposit" in text or "መሙያ" in text:
        deposit_instruction = (
            "💰 **Telebirr Deposit / የክፍያ መመሪያ:**\n\n"
            "የፈለጉትን የገንዘብ መጠን ወደዚህ የቴሌብር አካውንት ያስገቡ:\n"
            "📱 **Telebirr Number:** `0913701367`\n"
            "👤 **Account Name:** ELIAS FIKADU\n\n"
            "Kaffaltii erga raawwattanii booda, **Screenshot** ykn **Transaction ID** botii kanaaf ergaa. Admin ilaalee isiniif guuta!"
        )
        await update.message.reply_text(deposit_instruction, parse_mode="Markdown")
        return GET_DEPOSIT
    elif "Send FAN" in text or "ቁጥር" in text:
        await update.message.reply_text("📥 Maaloo lakkofsa FIN (12 digits) ykn FAN (16 digits) galchaa:")
        return GET_FAN
    elif "Help" in text or "እርዳታ" in text:
        await update.message.reply_text("📞 Admin Contact: @Urjii_Admin")
        return MAIN_MENU
    elif text.isdigit() and (len(text) == 12 or len(text) == 16):
        return await process_fan_input(update, context, text)
    else:
        await update.message.reply_text("Maaloo menu irraa filadhaa / እባክዎ ከምናሌው ይምረጡ::")
        return MAIN_MENU

async def handle_fan_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fan_number = update.message
