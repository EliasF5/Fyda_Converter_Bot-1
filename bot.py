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

# Flask Server for Render hosting
flask_app = Flask('')

@flask_app.route('/')
def home(): 
    return "Bot is running live!"

def run_flask(): 
    flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8647607353:AAHbJYHAYMRtLDTduLNYghgSC_Q9-UPjZrY"

MAIN_MENU, GET_FAN, GET_OTP, GET_DEPOSIT = range(4)
user_data = {}

def get_user_profile(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 100, 
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
        "👋 **Welcome!**\n\n"
        "Send your **FCN/FAN** (16 digits) to receive OTP.\n\n"
        "👤 **Account Name:** ELIAS FIKADU\n"
        "📱 **Telebirr Number:** `0913701367`"
    )
    
    keyboard = [
        [KeyboardButton("🔑 Send FAN / FIN")],
        [KeyboardButton("⚙️ Settings"), KeyboardButton("💰 Balance")],
        [KeyboardButton("💳 Deposit"), KeyboardButton("📞 Help")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    return MAIN_MENU

async def handle_menu_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    
    if text == "⚙️ Settings":
        # Settings code...
        return MAIN_MENU
    elif text == "💰 Balance":
        await update.message.reply_text(f"💵 **Your Current Wallet Balance:** {prof['balance']} ETB")
        return MAIN_MENU
    elif text == "💳 Deposit":
        await update.message.reply_text("💰 Send your Transaction ID or Screenshot here after paying to **ELIAS FIKADU (0913701367)**.")
        return GET_DEPOSIT
    elif text == "🔑 Send FAN / FIN":
        await update.message.reply_text("Enter your 12-digit FIN or 16-digit FAN number:")
        return GET_FAN
    elif text == "📞 Help":
        await update.message.reply_text("📞 Contact Admin: @Urjii_Admin")
        return MAIN_MENU
    return MAIN_MENU

async def handle_fan_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fan_number = update.message.text.strip()
    if not fan_number.isdigit() or len(fan_number) < 12:
        await update.message.reply_text("❌ Invalid number. Try again:")
        return GET_FAN
    return await process_fan_input(update, context, fan_number)

async def process_fan_input(update: Update, context: ContextTypes.DEFAULT_TYPE, fan_number):
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    
    if prof["balance"] < 15:
        await update.message.reply_text("❌ Balance keessan gahaa miti. Maaloo dursee herrega guuttadhaaa.")
        return MAIN_MENU
        
    status_msg = await update.message.reply_text("Sarvarii Fayda irraa OTP gaafachaa jira... 🔄")
    
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True, args=[
        "--no-sandbox", 
        "--disable-setuid-sandbox", 
        "--disable-blink-features=AutomationControlled"
    ])
    
    # Stealth mode gargaaramnee eegumsa bot akka inni dabarru goona
    context_page = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = await context_page.new_page()
    await stealth_async(page)
    
    try:
        await page.goto("https://fayda.gov.et/portal", timeout=30000, wait_until="networkidle")
        
        # Maaloo asirratti selector-riin 'input[name=fan]' sirrii ta'uu mirkaneessi
        await page.fill("input[name='fan']", fan_number)
        await page.click("button[type='submit']")
        await asyncio.sleep(5)
        
        prof["session"] = {"playwright": p, "browser": browser, "page": page, "fan": fan_number}
        await status_msg.edit_text("✅ **OTP Sent successfully!**\n\n📩 Maaloo OTP daqiiqaa 2 keessatti galchaa:")
        return GET_OTP
    except Exception as e:
        logging.error(f"Fayda Connection Error: {e}")
        await browser.close()
        await p.stop()
        await status_msg.edit_text("❌ **Sarvariin Fayda deebii dhorkateera (Eegumsa Webiitiin).**\nMaaloo xiqqoo turee irra deebi'i. Kaffaltiin keessan hin hir'anne.")
        prof["session"] = {}
        return MAIN_MENU

async def handle_otp_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp_code = update.message.text.strip()
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    
    if "page" not in prof["session"]:
        await update.message.reply_text("❌ Session expired. Deebisaa FAN galchaa.")
        return MAIN_MENU

    status_msg = await update.message.reply_text("Mirkaneessaa jira... ⏳")
    page = prof["session"]["page"]
    
    try:
        await page.fill("input[name='otp']", otp_code)
        await page.click("button[type='submit']")
        await asyncio.sleep(5)
        
        # Maqaa guutuu fudhachuuf
        final_name = await page.locator("#user-name").inner_text()
        prof["balance"] -= 35 
        
        # PDF Uumuu fi erguu...
        await update.message.reply_text(f"✅ Hojii milkaaa'e! Maqaa: {final_name}")
    except Exception as e:
        await status_msg.edit_text("❌ **OTP Dogoggora ykn weebsaayitiin Fayda kufeera.**")
    finally:
        await prof["session"]["browser"].close()
        await prof["session"]["playwright"].stop()
        prof["session"] = {}
        
    return MAIN_MENU

async def handle_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    prof["balance"] += 50
    await update.message.reply_text("✅ Deposit received. 50 ETB added.")
    return MAIN_MENU

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_options)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_options)],
            GET_FAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fan_state)],
            GET_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_otp_state)],
            GET_DEPOSIT: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_deposit)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    app.add_handler(conv_handler)
    app.run_polling()
