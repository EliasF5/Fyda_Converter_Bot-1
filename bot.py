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
    elif "Balance" in text or "ሂሳብ" in text or "💰" in text:
        await update.message.reply_text(f"💵 **Your Balance / የርስዎ ሂሳብ:** {prof['balance']} ETB", parse_mode="Markdown")
        return MAIN_MENU
    elif "Deposit" in text or "መሙያ" in text:
        deposit_instruction = (
            "💰 **Telebirr Deposit / የክፍያ መመሪያ:**\n\n"
            "የፈለጉትን የገንዘብ መጠን ወደዚህ የቴሌብር አካውንት ያስገቡ:\n"
            "📱 **Telebirr Number:** `0913701367`\n"
            "👤 **Account Name:** ELIAS FIKADU\n\n"
            "Kaffaltii erga raawwattanii booda, **Transaction ID** (SMS) ykn **Screenshot** botii kanaaf kallaattiin ergaa!"
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
    fan_number = update.message.text.strip()
    if not fan_number.isdigit() or len(fan_number) not in [12, 16]:
        await update.message.reply_text("❌ Lakkofsi dogoggora! Lakkofsa sirrii galchaa (12 ykn 16 digits):")
        return GET_FAN
    return await process_fan_input(update, context, fan_number)

async def process_fan_input(update: Update, context: ContextTypes.DEFAULT_TYPE, fan_number):
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    
    if prof["balance"] < 15:
        await update.message.reply_text("❌ Balance keessan gahaa miti. Maaloo dursee herrega guuttadhaaa.")
        return MAIN_MENU
        
    status_msg = await update.message.reply_text("🌐 Connecting to Fayda Server... 🔄")
    
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"])
    context_page = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    page = await context_page.new_page()
    await stealth_async(page)
    
    try:
        await page.goto("https://fayda.gov.et/portal", timeout=30000, wait_until="networkidle")
        await page.fill("input[name='fan']", fan_number)
        await page.click("button[type='submit']")
        await asyncio.sleep(4)
        
        prof["session"] = {"playwright": p, "browser": browser, "page": page, "fan": fan_number}
        await status_msg.edit_text("✅ **OTP Sent Successfully! / ኦቲፒ ተልኳል!**\n\n📩 Maaloo OTP lakkofsa 6 dhufe asirratti ergaa:")
        return GET_OTP
    except Exception as e:
        logging.error(f"Fayda Connection Error: {e}")
        await browser.close()
        await p.stop()
        await status_msg.edit_text("❌ **Sarvariin Fayda deebii dhorkateera.**\nMaaloo daqiiqaa muraasa booda irra deebi'ii yaali.")
        prof["session"] = {}
        return MAIN_MENU

async def handle_otp_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp_code = update.message.text.strip()
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    
    if "page" not in prof["session"]:
        await update.message.reply_text("❌ Session Expired! Irra deebi'ii yaali.")
        return MAIN_MENU

    status_msg = await update.message.reply_text("🔄 Checking OTP & Generating PDF... ⏳")
    page = prof["session"]["page"]
    fan_number = prof["session"]["fan"]
    
    try:
        await page.fill("input[name='otp']", otp_code)
        await page.click("button[type='submit']")
        await asyncio.sleep(5)
        
        final_name = await page.locator("#user-name").inner_text()
        prof["balance"] -= 35 
    except Exception as e:
        await status_msg.edit_text("❌ **OTP Dogoggora ykn sarvariin addaan cite!**")
        await prof["session"]["browser"].close()
        await prof["session"]["playwright"].stop()
        prof["session"] = {}
        return MAIN_MENU
    finally:
        try:
            await prof["session"]["browser"].close()
            await prof["session"]["playwright"].stop()
        except:
            pass

    safe_name = final_name.replace(" ", "_")
    pdf_path = f"{safe_name}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
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

async def handle_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    prof["balance"] += 50
    await update.message.reply_text("✅ **Kaffaltiin keessan fudhatameera!**\n50 ETB Balance keessan irratti dabalameera.")
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
    elif query.data == "menu_back":
        await query.message.delete()
        return MAIN_MENU
        
    settings_text = f"⚙️ **Settings Updated:**\nFormat: {prof['output_mode']}\nPhoto: {prof['photo_mode']}"
    keyboard = [
        [InlineKeyboardButton("PDF Only", callback_data="toggle_out_pdf"), InlineKeyboardButton("PDF + ID ID", callback_data="toggle_out_both")],
        [InlineKeyboardButton("Color Photo", callback_data="toggle_photo_color"), InlineKeyboardButton("Grey Photo", callback_data="toggle_photo_grey")],
        [InlineKeyboardButton("❌ Close", callback_data="menu_back")]
    ]
    await query.edit_message_text(settings_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_options), MessageHandler(filters.PHOTO, handle_deposit)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_options), CallbackQueryHandler(settings_callback)],
            GET_FAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fan_state)],
            GET_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_otp_state)],
            GET_DEPOSIT: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_deposit)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    app.add_handler(conv_handler)
    print("Bot is successfully running...")
    app.run_polling()
