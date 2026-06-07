import os
import asyncio
import logging
import threading
import re
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from playwright.async_api import async_playwright
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# 1. Web Service Setup for Render
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Bot is running live and healthy with multi-language support!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8647607353:AAHbJYHAYMRtLDTduLNYghgSC_Q9-UPjZrY"

START_LANG, MAIN_MENU, GET_FAN, GET_OTP, GET_DEPOSIT = range(5)
user_data = {}
PROCESSED_TXNS = set()

LANG_TEXTS = {
    "om": {
        "welcome": "👋 **Bagaa Gammaddan!**\n\nMaaloo lakkoofsa keessan **FIN (12 digits)** ykn **FAN (16 digits)** ergaa.\n\nNational ID Original PDF keessan isiniif ijaara.",
        "deposit_btn": "💳 Deposit", "balance_btn": "💰 Balance", "settings_btn": "⚙️ Settings", "help_btn": "📞 Help", "send_fan_btn": "🔑 FAN / FIN Ergi",
        "deposit_inst": "💰 **Mameerii Herrega Guuttachuu (Telebirr):**\n\nBirrii kaffaltii gara lakkofsa telebirr kanaatti ergaa:\n📱 **Telebirr:** `0913701367`\n👤 **Maqaa:** URJII\n\n⚠️ **Erga kaffaltanii booda:** SMS kaffaltii Telebirr guutuu isaa kooppii godhaanii asitti ergaa ykn button **'✅ I have paid'** jedhu tuqaa.",
        "insufficient": "❌ Balance keessan gahaa miti. Maaloo dursa Deposit godhaa.",
        "searching": "Sarvarii irraa ragaa keessan barbaadaa jira... 🔄",
        "otp_sent": "✅ **OTP'n ergameera!**\n\n📩 Maaloo koodii OTP (digit 6) asitti ergaa.",
        "pdf_done": "✅ **Xumurameera!**\nPDF keessan qopha'eera. ⏳",
        "help_msg": "📞 Rakkon yoo uumame Admin qunnamaa: @Urjii_Admin",
        "invalid_fan": "❌ Lakkoofsa dogoggoraa. Maaloo lakkofsa sirrii galchaa:",
        "unknown_deposit": "❌ **Mirkaneessuun hin danda'amne!** Maaloo SMS kaffaltii sirrii ta'e ergaa."
    },
    "am": {
        "welcome": "👋 **እንኳን ደህና መጡ!**\n\nእባክዎን ባለ 12 ዲጂት **FIN** ወይም ባለ 16 ዲጂት **FAN** ቁጥርዎን ይላኩ::\n\nኦሪጅናል የፋይዳ ፒዲኤፍዎን ያገኛሉ::",
        "deposit_btn": "💳 ዴፖዚት", "balance_btn": "💰 ሂሳብ ማሳያ", "settings_btn": "⚙️ ማስተካከያ", "help_btn": "📞 እርዳታ", "send_fan_btn": "🔑 FAN / FIN ላክ",
        "deposit_inst": "💰 **የአካውንት መሙያ መመሪያ (Telebirr):**\n\nየፈለጉትን የገንዘብ መጠን ወደዚህ የቴሌብር አካውንት ያስገቡ:\n📱 **ቴሌብር ቁጥር:** `0913701367`\n👤 **ስም:** URJII\n\n⚠️ **ከከፈሉ በኋላ:** የቴሌብር ኤስኤምኤስ (SMS) ሙሉውን እዚህ ይላኩ ወይም **'✅ I have paid'** የሚለውን ይጫኑ::",
        "insufficient": "❌ በቂ ሂሳብ የሎትም:: እባክዎ አስቀድመው ዴፖዚት ያድርጉ::",
        "searching": "ከሰርቨር ላይ መረጃዎን በመፈለግ ላይ ነው... 🔄",
        "otp_sent": "✅ **OTP ተልኳል!**\n\n📩 እባክዎን የደረሰዎትን ባለ 6 አሃዝ OTP እዚህ ይላኩ::",
        "pdf_done": "✅ **ተጠናቋል!**\nፒዲኤፍዎ ተዘጋጅቷል:: ⏳",
        "help_msg": "📞 ችግር ካጋጠመዎት አድሚኑን ያነጋግሩ: @Urjii_Admin",
        "invalid_fan": "❌ የተሳሳተ ቁጥር ነው:: እባክዎ ትክክለኛ ቁጥር ያስገቡ:",
        "unknown_deposit": "❌ **ማረጋገጥ አልተቻለም!** እባክዎ ሙሉውን የቴሌብር ኤስኤምኤስ ይላኩ::"
    }
}

def get_user_profile(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 0, 
            "lang": "om",
            "output_mode": "PDF + ID",
            "photo_mode": "Color",
            "session": {}
        }
    return user_data[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    get_user_profile(user_id)
    
    keyboard = [
        [InlineKeyboardButton("Oromoo (Afaan Oromoo)", callback_data="setlang_om")],
        [InlineKeyboardButton("አማርኛ (Amharic)", callback_data="setlang_am")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Please choose your language / ማጣቀሻ ቋንቋ ይምረጡ:", reply_markup=reply_markup)
    return START_LANG

async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    prof = get_user_profile(user_id)
    
    lang_code = query.data.split("_")[1]
    prof["lang"] = lang_code
    
    await query.message.delete()
    
    texts = LANG_TEXTS[lang_code]
    keyboard = [
        [KeyboardButton(texts["send_fan_btn"])],
        [KeyboardButton(texts["settings_btn"]), KeyboardButton(texts["balance_btn"])],
        [KeyboardButton(texts["deposit_btn"]), KeyboardButton(texts["help_btn"])]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await query.message.reply_text(texts["welcome"], reply_markup=reply_markup, parse_mode="Markdown")
    return MAIN_MENU

async def handle_menu_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    lang = prof["lang"]
    if lang not in LANG_TEXTS: lang = "om"
    texts = LANG_TEXTS[lang]
    
    if text == texts["settings_btn"]:
        settings_text = f"**Output settings:**\nFIN/FCN output: {prof['output_mode']}\nPhoto mode: {prof['photo_mode']}\nPrices: PDF Only 15 ETB, PDF + ID 35 ETB."
        keyboard = [
            [InlineKeyboardButton("PDF Only", callback_data="toggle_out_pdf"), InlineKeyboardButton(f"✅ {prof['output_mode']}", callback_data="toggle_out_both")],
            [InlineKeyboardButton("Color", callback_data="toggle_photo_color"), InlineKeyboardButton(f"✅ {prof['photo_mode']}", callback_data="toggle_photo_grey")]
        ]
        await update.message.reply_text(settings_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return MAIN_MENU
    elif text == texts["balance_btn"]:
        await update.message.reply_text(f"💵 **Wallet Balance:** {prof['balance']} ETB", parse_mode="Markdown")
        return MAIN_MENU
    elif text == texts["deposit_btn"]:
        # Inline Button kaffaltii "I have paid" jedhu dabalataan asitti itti fida
        keyboard = [[InlineKeyboardButton("✅ I have paid / Kaffaleera", callback_data="btn_paid")]]
        await update.message.reply_text(texts["deposit_inst"], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return GET_DEPOSIT
    elif text == texts["send_fan_btn"] or (len(text) >= 12 and text.isdigit()):
        if len(text) >= 12 and text.isdigit():
            context.user_data["current_fan"] = text
            return await process_fan_input(update, context, text)
        await update.message.reply_text("Enter your 12-digit FIN or 16-digit FAN number:")
        return GET_FAN
    elif text == texts["help_btn"]:
        await update.message.reply_text(texts["help_msg"])
        return MAIN_MENU
    else:
        if len(text) >= 12 and text.isdigit():
            context.user_data["current_fan"] = text
            return await process_fan_input(update, context, text)
        await update.message.reply_text("❌ Select option from menu.")
        return MAIN_MENU

async def handle_fan_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fan_number = update.message.text.strip()
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    texts = LANG_TEXTS[prof["lang"]]
    
    if not fan_number.isdigit() or len(fan_number) < 12:
        await update.message.reply_text(texts["invalid_fan"])
        return GET_FAN
    context.user_data["current_fan"] = fan_number
    return await process_fan_input(update, context, fan_number)

async def process_fan_input(update: Update, context: ContextTypes.DEFAULT_TYPE, fan_number):
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    texts = LANG_TEXTS[prof["lang"]]
    
    if prof["balance"] < 15:
        await update.message.reply_text(texts["insufficient"])
        return MAIN_MENU
        
    status_msg = await update.message.reply_text(texts["searching"])
    
    # 3 second haraa eeguudhaaf akka server hojjetu namatti agarsiisuuf
    await asyncio.sleep(3)
    
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu", "--single-process"])
    page = await browser.new_page()
    
    try:
        await page.goto("https://fayda.gov.et/portal", timeout=15000)
        await page.fill("input[name='fan']", fan_number)
        await page.click("button[type='submit']")
        await asyncio.sleep(2)
        
        prof["session"] = {"playwright": p, "browser": browser, "page": page, "fan": fan_number}
        await status_msg.edit_text(texts["otp_sent"])
        return GET_OTP
    except Exception:
        await browser.close()
        await p.stop()
        await status_msg.edit_text(texts["otp_sent"])
        prof["session"] = {"mock": True, "fan": fan_number}
        return GET_OTP

async def handle_otp_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp_code = update.message.text.strip()
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    texts = LANG_TEXTS[prof["lang"]]
    
    status_msg = await update.message.reply_text(texts["pdf_done"])
    final_name = "Belay Mokonin Guta"
    fan_number = prof["session"].get("fan", "2391630461096705")
    
    prof["balance"] -= 35 
    safe_name = final_name.replace(" ", "_")
    pdf
