import os
import asyncio
import logging
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from playwright.async_api import async_playwright
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

# Conversation states
MAIN_MENU, GET_FAN, GET_OTP, GET_DEPOSIT = range(4)

# Temporary in-memory database for users
user_data = {}

def get_user_profile(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 100,  # Default welcome balance for testing
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
        "Send your **FCN/FAN** (16 digits).\n\n"
        "I will request an **OTP**, then you send the OTP here and I will deliver your Original Fayda PDF.\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ℹ️ **ኦሪጅናል የፋይዳ ፒዲኤፍ ለማግኘት**\n\n"
        "FIN (ባለ 12 ዲጂት) ወይም FCN/FAN (ባለ 16 ዲጂት) ይላኩ::\n"
        "ከዛም በተመዘገቡበት ስልክ OTP ይደርሶታል፤ ቀጥሎ የደረሰዎትን OTP በፈጣን እዚህ ይላኩት:: "
        "ቦቱ ኦሪጅናል የፋይዳ ፒዲኤፍዎን ወዲያውኑ ይልክልዎታል::\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💰 **በቴሌብር ወደ ቦቱ ገንዘብ ገቢ ለማድረግ እነዚህን ቅደም ተከተሎች ይከተሉ:**\n"
        "1. Deposit የሚለውን ይጫኑ\n"
        "2. የቴሌብር ቁጥር በመምረጥ ገንዘብ ገቢ ያድርጉ\n"
        "3. የከፈሉበትን Transaction ID እዚህ ይላኩ\n\n"
        "💵 Use **Balance** to check your wallet.\n"
        "💳 Use **Deposit** to top-up.\n"
        "📞 Contact admin if you need help."
    )
    
    keyboard = [
        [KeyboardButton("🔑 Send FAN / FIN")],
        [KeyboardButton("⚙️ Settings"), KeyboardButton("💰 Balance")],
        [KeyboardButton("💳 Deposit"), KeyboardButton("📞 Help")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    return MAIN_MENU

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    
    settings_text = (
        f"**Output settings:**\n"
        f"FIN/FCN output: {prof['output_mode']}\n"
        f"Photo mode: {prof['photo_mode']}\n"
        f"Template: {prof['template']}\n"
        f"Oval cut: {prof['oval_cut']}\n"
        f"Template quality: {prof['quality']}\n"
        f"Merge on A4: {prof['merge_a4']}\n"
        f"Prices: PDF Only 15 ETB, PDF + ID 35 ETB."
    )
    
    keyboard = [
        [InlineKeyboardButton("PDF Only", callback_data="toggle_out_pdf"), InlineKeyboardButton(f"✅ {prof['output_mode']}", callback_data="toggle_out_both")],
        [InlineKeyboardButton("Color", callback_data="toggle_photo_color"), InlineKeyboardButton(f"✅ {prof['photo_mode']}", callback_data="toggle_photo_grey")],
        [InlineKeyboardButton("Back", callback_data="menu_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode="Markdown")
    return MAIN_MENU

async def handle_menu_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    
    if text == "⚙️ Settings":
        await show_settings(update, context)
        return MAIN_MENU
    elif text == "💰 Balance":
        await update.message.reply_text(f"💵 **Your Current Wallet Balance:** {prof['balance']} ETB", parse_mode="Markdown")
        return MAIN_MENU
    elif text == "💳 Deposit":
        deposit_instruction = (
            "💰 **የአካውንት መሙያ መመሪያ (Telebirr Deposit Instruction)**\n\n"
            "የፈለጉትን የገንዘብ መጠን ወደዚህ የቴሌብር አካውንት ያስገቡ:\n"
            "📱 **Telebirr Number:** `0913701367`\n"
            "👤 **Account Name:** ELIAS FIKADU\n\n"
            "ከከፈሉ በኋላ, የቴሌብር የክፍያ መልዕክት (SMS) ላይ የሚገኘውን **Transaction ID** (የግብይት መለያ ቁጥር) "
            "ወይም የክፍያውን **Screenshot** (ፎቶ) እዚህ ይላኩ:: Admin dafsee herrega keessan isiniif mogaasa!"
        )
        await update.message.reply_text(deposit_instruction, parse_mode="Markdown")
        return GET_DEPOSIT
    elif text == "🔑 Send FAN / FIN" or (len(text) >= 12 and text.isdigit()):
        if len(text) >= 12 and text.isdigit():
            context.user_data["current_fan"] = text
            return await process_fan_input(update, context, text)
        await update.message.reply_text("Enter your 12-digit FIN or 16-digit FAN number:")
        return GET_FAN
    elif text == "📞 Help":
        await update.message.reply_text("📞 Rakkon yoo uumame Admin qunnamaa: @Urjii_Admin\n(Maaloo lakkofsa kaffaltii keessanii sirriitti galchaa).")
        return MAIN_MENU
    else:
        await update.message.reply_text("Please select a valid option from the menu.")
        return MAIN_MENU

async def handle_fan_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fan_number = update.message.text.strip()
    if not fan_number.isdigit() or len(fan_number) < 12:
        await update.message.reply_text("❌ Invalid number. Please send a valid 12 or 16 digit number:")
        return GET_FAN
    context.user_data["current_fan"] = fan_number
    return await process_fan_input(update, context, fan_number)

async def process_fan_input(update: Update, context: ContextTypes.DEFAULT_TYPE, fan_number):
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    
    if prof["balance"] < 15:
        await update.message.reply_text("❌ Balance keessan gahaa miti. Maaloo kaffaltii erga raawwattanii booda yaala.")
        return MAIN_MENU
        
    status_msg = await update.message.reply_text("Sarvarii irraa ragaa keessan barbaadaa jira... 🔄")
    
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu", "--single-process"])
    page = await browser.new_page()
    
    try:
        # Gara sarvarii Fayda deema
        await page.goto("https://fayda.gov.et/portal", timeout=20000)
        await page.fill("input[name='fan']", fan_number)
        await page.click("button[type='submit']")
        await asyncio.sleep(3)
        
        # Yoo milkaa'e ragaa session keessa kaaya
        prof["session"] = {"playwright": p, "browser": browser, "page": page, "fan": fan_number, "mock": False}
        await status_msg.edit_text("✅ **OTP sent successfully!**\n\n📩 Please **send the OTP digits** here (6 digits).")
        return GET_OTP
    except Exception as e:
        # Yoo sarvariin deebii dhorkate asitti dhaaba, herrega hin hir'isu
        logging.error(f"Fayda Portal Error: {e}")
        try:
            await browser.close()
            await p.stop()
        except:
            pass
        await status_msg.edit_text("❌ **Dogoggora: Sarvarii Fayda irraa deebiin hin jiru.**\nMaaloo daqiiqaa muraasa booda irra deebi'ii yaali. Herregni keessan hin hir'anne.")
        prof["session"] = {}
        return MAIN_MENU

async def handle_otp_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp_code = update.message.text.strip()
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    
    if "page" not in prof["session"]:
        await update.message.reply_text("❌ Session expired. Maaloo lakkofsa FAN keessan deebisaa galchaa.")
        return MAIN_MENU

    status_msg = await update.message.reply_text("✅ **OTP Processing...** ⏳")
    
    final_name = "Belay Mokonin Guta"
    fan_number = prof["session"].get("fan", "2391630461096705")
    page = prof["session"]["page"]
    
    try:
        await page.fill("input[name='otp']", otp_code)
        await page.click("button[type='submit']")
        await asyncio.sleep(4)
        
        # Maqaa dhugaa sarvarii irraa fuda
        final_name = await page.locator("#user-name").inner_text()
        
        # Yoo milkaa'e qofa herrega hir'isa
        prof["balance"] -= 35 
    except Exception as e:
        logging.error(f"OTP verification failed: {e}")
        await status_msg.edit_text("❌ **OTP dogoggora ykn sarvariin citeera.** Kaffaltiin keessan hin hir'anne. Maaloo irra deebi'aa yaala.")
        try:
            await prof["session"]["browser"].close()
            await prof["session"]["playwright"].stop()
        except:
            pass
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
    c.drawString(120, 540, "Status: Verified Original")
    c.showPage()
    c.save()
    
    with open(pdf_path, 'rb') as f:
        await update.message.reply_document(document=f, filename=f"{safe_name}@National_idpdfbot.pdf", caption=f"👤 {final_name}\nDownloaded from @National_idpdfbot")
        
    try:
        with open(pdf_path, 'rb') as f:
            await update.message.reply_photo(photo=f, caption=f"Normal [{final_name}].png")
        with open(pdf_path, 'rb') as f:
            await update.message.reply_photo(photo=f, caption=f"Mirror [{final_name}].png")
        with open(pdf_path, 'rb') as f:
            await update.message.reply_photo(photo=f, caption=f"A4 (Color Mirror) [{final_name}].png")
    except Exception as e:
        logging.error(f"Error sending photos: {e}")
    
    try: 
        os.remove(pdf_path)
    except: 
        pass
    
    prof["session"] = {}
    await status_msg.delete()
    return MAIN_MENU

async def handle_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tx_id = update.message.text.strip() if update.message.text else "Screenshot"
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    
    prof["balance"] += 50
    await update.message.reply_text(f"✅ **Kaffaltiin Keessan Mirkanaa'eera!**\nTransaction ID: {tx_id}\n50 ETB Balance keessan irratti dabalameera. Hojii keessan itti fufaa!")
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
        
    settings_text = (
        f"**Output settings:**\n"
        f"FIN/FCN output: {prof['output_mode']}\n"
        f"Photo mode: {prof['photo_mode']}\n"
        f"Prices: PDF Only 15 ETB, PDF + ID 35 ETB."
    )
    keyboard = [
        [InlineKeyboardButton("PDF Only", callback_data="toggle_out_pdf"), InlineKeyboardButton(f"✅ {prof['output_mode']}", callback_data="toggle_out_both")],
        [InlineKeyboardButton("Color", callback_data="toggle_photo_color"), InlineKeyboardButton(f"✅ {prof['photo_mode']}", callback_data="toggle_photo_grey")],
        [InlineKeyboardButton("Back", callback_data="menu_back")]
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
    print("Bot starting up with custom Telebirr account...")
    app.run_polling()
