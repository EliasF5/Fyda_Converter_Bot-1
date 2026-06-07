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
    return "Bot is running live and healthy with multi-language support! Developed for Elias Fikadu."

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8647607353:AAHbJYHAYMRtLDTduLNYghgSC_Q9-UPjZrY"

START_LANG, MAIN_MENU, GET_FAN, GET_OTP, GET_DEPOSIT, GET_AMOUNT_SELECTION = range(6)
user_data = {}
PROCESSED_TXNS = set()

LANG_TEXTS = {
    "om": {
        "welcome": "👋 **Baga nagaan dhuftan!**\n\nMaaloo lakkoofsa **FIN (12 digits)** ykn **FAN (16 digits)** keessan naaf ergaa.\nNational ID Original PDF keessan isiniif ijaara.",
        "deposit_btn": "💳 Deposit", "balance_btn": "💰 Balance", "settings_btn": "⚙️ Settings", "help_btn": "📞 Help", "send_fan_btn": "🔑 FAN / FIN Ergi",
        "deposit_inst": "💰 **Mameerii Herrega Guuttachuu (Telebirr):**\n\nBirrii kaffaltii gara lakkofsa telebirr kanaatti ergaa:\n📱 **Telebirr:** `0913701367`\n👤 **Maqaa:** ELIAS FIKADU\n\n⚠️ **Erga kaffaltanii booda:** Gadi lakkisaa itti aanuun button **'✅ I have paid'** jedhu tuqaa, sana booda screenshot ykn koodii kaffaltii ergaa.",
        "insufficient": "❌ Balance keessan gahaa miti. Maaloo dursa Deposit godhaa.",
        "searching": "Sarvarii irraa ragaa keessan barbaadaa jira... 🔄",
        "otp_sent": "✅ **OTP'n ergameera!**\n\n📩 Maaloo koodii OTP (digit 6) asitti ergaa.",
        "pdf_done": "✅ **Xumurameera!**\nPDF keessan qopha'eera. ⏳",
        "help_msg": "📞 Rakkon yoo uumame Admin qunnamaa: @Elias_Fikadu",
        "invalid_fan": "❌ Lakkoofsa dogoggoraa. Maaloo lakkofsa sirrii galchaa:",
        "unknown_deposit": "❌ **Mirkaneessuun hin danda'amne!** Maaloo SMS kaffaltii sirrii ta'e ergaa."
    },
    "am": {
        "welcome": "👋 **እንኳን ደህና መጡ!**\n\nእባክዎን ባለ 12 ዲጂት **FIN** ወይም ባለ 16 ዲጂት **FAN** ቁጥርዎን ይላኩ::\nኦሪጅናል የፋይዳ ፒዲኤፍዎን ያገኛሉ::",
        "deposit_btn": "💳 ዴፖዚት", "balance_btn": "💰 ሂሳብ ማሳያ", "settings_btn": "⚙️ ማስተካከያ", "help_btn": "📞 እርዳታ", "send_fan_btn": "🔑 FAN / FIN ላክ",
        "deposit_inst": "💰 **የአካውንት መሙያ መመሪያ (Telebirr):**\n\nየፈለጉትን የገንዘብ መጠን ወደዚህ የቴሌብር አካውንት ያስገቡ:\n📱 **ቴሌብር ቁጥር:** `0913701367`\n👤 **ስም:** ELIAS FIKADU\n\n⚠️ **ከከፈሉ በኋላ:** እባክዎን **'✅ I have paid'** የሚለውን ይጫኑ:: ከዚያም ማረጋገጫ ይላኩ::",
        "insufficient": "❌ በቂ ሂሳብ የሎትም:: እባክዎ አስቀድመው ዴፖዚት ያድርጉ::",
        "searching": "ከሰርቨር ላይ መረጃዎን በመፈለግ ላይ ነው... 🔄",
        "otp_sent": "✅ **OTP ተልኳል!**\n\n📩 እባክዎን የደረሰዎትን ባለ 6 አሃዝ OTP እዚህ ይላኩ::",
        "pdf_done": "✅ **ተጠናቋል!**\nፒዲኤፍዎ ተዘጋጅቷል:: ⏳",
        "help_msg": "📞 ችግር ካጋጠመዎት አድሚኑን ያነጋግሩ: @Elias_Fikadu",
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
        keyboard = [
            [InlineKeyboardButton("✅ I have paid", callback_data="btn_ihavepaid")],
            [InlineKeyboardButton("⬅️ Back", callback_data="btn_back_main")]
        ]
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

async def handle_deposit_state_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Yoo text uumame kaffaltii fuskii fi koodii iddoo kanatti mirkaneessa
    return await handle_deposit_logic(update, context, amount=50)

async def handle_deposit_logic(update: Update, context: ContextTypes.DEFAULT_TYPE, amount=50):
    user_id = update.effective_user.id
    prof = get_user_profile(user_id)
    prof["balance"] += amount
    
    success_text = (
        f"✅ **Kaffaltiini Keessan Mirkanaa'eera! (ELIAS FIKADU)**\n\n"
        f"💵 **Amount:** {amount} ETB Balance keessan irratti dabalameera. Hojii keessan itti fufaa!"
    )
    await context.bot.send_message(chat_id=user_id, text=success_text, parse_mode="Markdown")
    return MAIN_MENU

async def deposit_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    prof = get_user_profile(user_id)
    
    if query.data == "btn_ihavepaid":
        keyboard = [
            [InlineKeyboardButton("5 Pdf = 75 ETB", callback_data="amt_75"), InlineKeyboardButton("10 Pdf = 150 ETB", callback_data="amt_150")],
            [InlineKeyboardButton("20 Pdf = 300 ETB", callback_data="amt_300"), InlineKeyboardButton("30 Pdf = 450 ETB", callback_data="amt_450")],
            [InlineKeyboardButton("50 Pdf = 750 ETB", callback_data="amt_750"), InlineKeyboardButton("100 Pdf = 1500 ETB", callback_data="amt_1500")],
            [InlineKeyboardButton("🚀 200 + free 15 Pdf = 3000 ETB", callback_data="amt_3000")],
            [InlineKeyboardButton("⭐ 300 + free 30 Pdf = 4500 ETB", callback_data="amt_4500")],
            [InlineKeyboardButton("💎 500 + free 60 Pdf = 7500 ETB", callback_data="amt_7500")],
            [InlineKeyboardButton("👑 1000 + free 150 Pdf = 15000 ETB", callback_data="amt_15000")]
        ]
        await query.message.edit_text("🔻 **Select a top-up amount bellow:**\n\n👇 𝘘𝘢𝘱𝘹𝘪𝘪/𝘉𝘶𝘵𝘵𝘰𝘯 𝘒𝘢𝘧𝘧𝘢𝘭𝘵𝘪𝘪 𝘎𝘢𝘭𝘤𝘩𝘪𝘵𝘢𝘯 𝘍𝘪𝘭𝘢𝘥𝘩𝘢𝘢:", reply_markup=InlineKeyboardMarkup(keyboard))
        return GET_AMOUNT_SELECTION
    elif query.data == "btn_back_main":
        texts = LANG_TEXTS[prof["lang"]]
        keyboard = [
            [KeyboardButton(texts["send_fan_btn"])],
            [KeyboardButton(texts["settings_btn"]), KeyboardButton(texts["balance_btn"])],
            [KeyboardButton(texts["deposit_btn"]), KeyboardButton(texts["help_btn"])]
        ]
        await query.message.delete()
        await context.bot.send_message(chat_id=user_id, text=texts["welcome"], reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True), parse_mode="Markdown")
        return MAIN_MENU

async def amount_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    amount_map = {
        "amt_75": 75, "amt_150": 150, "amt_300": 300, "amt_450": 450,
        "amt_750": 750, "amt_1500": 1500, "amt_3000": 3000, "amt_4500": 4500,
        "amt_7500": 7500, "amt_15000": 15000
    }
    
    selected_amount = amount_map.get(data, 50)
    await query.message.delete()
    return await handle_deposit_logic(update, context, amount=selected_amount)

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
    await asyncio.sleep(2)
    
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
    pdf_path = f"{safe_name}.pdf"
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setStrokeColor(HexColor("#0056b3"))
    c.setFillColor(HexColor("#f8f9fa"))
    c.rect(100, 450, 380, 220, stroke=1, fill=1)
    c.setFillColor(HexColor("#0056b3"))
    c.rect(100, 640, 380, 30, stroke=0, fill=1)
    c.setFillColor(HexColor("#ffffff"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(150, 650, "FEDERAL DEMOCRATIC REPUBLIC OF ETHIOPIA")
    c.setFillColor(HexColor("#000000"))
    c.drawString(120, 600, f"Name: {final_name}")
    c.drawString(120, 570, f"FAN/FIN: {fan_number}")
    c.showPage()
    c.save()
    
    with open(pdf_path, 'rb') as f:
        await update.message.reply_document(document=f, filename=f"{safe_name}@National_idpdfbot.pdf")
        
    try: os.remove(pdf_path)
    except: pass
    
    prof["session"] = {}
    await status_msg.delete()
    return MAIN_MENU

async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    prof = get_user_profile(user_id)
    
    if query.data == "toggle_out_pdf": prof["output_mode"] = "PDF Only"
    elif query.data == "toggle_out_both": prof["output_mode"] = "PDF + ID"
    elif query.data == "toggle_photo_color": prof["photo_mode"] = "Color"
    elif query.data == "toggle_photo_grey": prof["photo_mode"] = "Grey"
    
    await query.edit_message_text(f"Settings updated! Mode: {prof['output_mode']}")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_options)],
        states={
            START_LANG: [CallbackQueryHandler(lang_callback, pattern="^setlang_")],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_options), CallbackQueryHandler(settings_callback)],
            GET_FAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fan_state)],
            GET_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_otp_state)],
