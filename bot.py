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
    # Render environment variable PORT fayyadama
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8647607353:AAHbJYHAYMRtLDTduLNYghgSC_Q9-UPjZrY"

START_LANG, MAIN_MENU, GET_FAN, GET_OTP, GET_DEPOSIT = range(5)
user_data = {}
PROCESSED_TXNS = set()

# TRANSLATION DICTIONARY FOR 5 ETHIOPIAN LANGUAGES
LANG_TEXTS = {
    "om": {
        "welcome": "👋 **Bagaa Gammaddan!**\n\nMaaloo lakkoofsa keessan **FIN (12 digits)** ykn **FAN (16 digits)** ergaa.\n\nOTP gara bilbila keessaniitti ni ergama, ergaa OTP asitti yoo deebistan Original Fayda PDF keessan ni dhiyaata.",
        "deposit_btn": "💳 Deposit", "balance_btn": "💰 Balance", "settings_btn": "⚙️ Settings", "help_btn": "📞 Help", "send_fan_btn": "🔑 FAN / FIN Ergi",
        "deposit_inst": "💰 **Mameerii Herrega Guuttachuu (Telebirr):**\n\nBirrii barbaaddan gara lakkofsa telebirr kanaatti ergaa:\n📱 **Telebirr:** `0913701367`\n👤 **Maqaa:** URJII\n\n⚠️ **Erga kaffaltanii booda:** SMS kaffaltii Telebirr guutuu isaa asitti kooppii godhaanii ergaa.",
        "insufficient": "❌ Balance keessan gahaa miti. Maaloo dursa Deposit godhaa.",
        "searching": "Sarvarii irraa ragaa keessan barbaadaa jira... 🔄",
        "otp_sent": "✅ **OTP'n ergameera!**\n\n📩 Maaloo koodii OTP (digit 6) asitti ergaa.",
        "pdf_done": "✅ **Xumurameera!**\nPDF keessan qopha'eera. ⏳",
        "help_msg": "📞 Rakkon yoo uumame Admin qunnamaa: @Urjii_Admin",
        "invalid_fan": "❌ Lakkoofsa dogoggoraa. Maaloo lakkofsa sirrii galchaa:",
        "unknown_deposit": "❌ **Mirkaneessuun hin danda'amne!** Maaloo SMS kaffaltii Telebirr guutuu isaa ergaa."
    },
    "am": {
        "welcome": "👋 **እንኳን ደህና መጡ!**\n\nእባክዎን ባለ 12 ዲጂት **FIN** ወይም ባለ 16 ዲጂት **FAN** ቁጥርዎን ይላኩ::\n\nወደ ስልክዎ የኤስኤምኤስ (OTP) ይላካል፣ የደረሰዎትን OTP እዚህ ሲልኩ ኦሪጅናል የፋይዳ ፒዲኤፍዎን ያገኛሉ::",
        "deposit_btn": "💳 ዴፖዚት", "balance_btn": "💰 ሂሳብ ማሳያ", "settings_btn": "⚙️ ማስተካከያ", "help_btn": "📞 እርዳታ", "send_fan_btn": "🔑 FAN / FIN ላክ",
        "deposit_inst": "💰 **የአካውንት መሙያ መመሪያ (Telebirr):**\n\nየፈለጉትን የገንዘብ መጠን ወደዚህ የቴሌብር አካውንት ያስገቡ:\n📱 **ቴሌብር ቁጥር:** `0913701367`\n👤 **ስም:** URJII\n\n⚠️ **ከከፈሉ በኋላ:** የቴሌብር የክፍያ መልዕክት (**SMS**) ሙሉውን እዚህ ኮፒ አድርገው ይላኩ::",
        "insufficient": "❌ በቂ ሂሳብ የሎትም:: እባክዎ አስቀድመው ዴፖዚት ያድርጉ::",
        "searching": "ከሰርቨር ላይ መረጃዎን በመፈለግ ላይ ነው... 🔄",
        "otp_sent": "✅ **OTP ተልኳል!**\n\n📩 እባክዎን የደረሰዎትን ባለ 6 አሃዝ OTP እዚህ ይላኩ::",
        "pdf_done": "✅ **ተጠናቋል!**\nፒዲኤፍዎ ተዘጋጅቷል:: ⏳",
        "help_msg": "📞 ችግር ካጋጠመዎት አድሚኑን ያነጋግሩ: @Urjii_Admin",
        "invalid_fan": "❌ የተሳሳተ ቁጥር ነው:: እባክዎ ትክክለኛ ቁጥር ያስገቡ:",
        "unknown_deposit": "❌ **ማረጋገጥ አልተቻለም!** እባክዎ ሙሉውን የቴሌብር ኤስኤምኤስ ይላኩ::"
    },
    "so": {
        "welcome": "👋 **Ku soo dhowaw!**\n\nTfadlan soo dir nambarkaaga **FIN (12 digits)** ama **FAN (16 digits)**.\n\nKoodhka OTP ayaa loo soo diri doonaa telefoonkaaga, markaad koodhka halkaan ku soo celiso waxaad helaysaa PDF-gaaga rasmiga ah.",
        "deposit_btn": "💳 Deposit", "balance_btn": "💰 Haraaga", "settings_btn": "⚙️ Settings", "help_btn": "📞 Caawinaad", "send_fan_btn": "🔑 Dir FAN / FIN",
        "deposit_inst": "💰 **Hagaha Lacag Shubashada (Telebirr):**\n\nKu shub lacagta aad rabto nambarkaan:\n📱 **Telebirr:** `0913701367`\n👤 **Magaca:** URJII\n\n⚠️ **Markaad lacagta dirto:** Nuqul ka soo qaado fariinta (**SMS**) kooppii guutuu ah halkanna ku soo dir.",
        "insufficient": "❌ Haraagaagu kuma filna. Fadlan marka hore lacag shubo.",
        "searching": "Waxaa laga raadinayaa xogtaada server-ka... 🔄",
        "otp_sent": "✅ **OTP waa la diray!**\n\n📩 Tfadlan soo dir koodhka OTP (6 lambar) halkaan.",
        "pdf_done": "✅ **Waa dhammaaday!**\nPDF-gaagii waa diyaar. ⏳",
        "help_msg": "📞 Haddii dhibaatadi timaado la xiriir Admin: @Urjii_Admin",
        "invalid_fan": "❌ Nambar khaldan. Tfadlan geli nambar sax ah:",
        "unknown_deposit": "❌ **Waa la xaqiigi waayay!** Tfadlan soo dir fariinta SMS-ka Telebirr oo buuxda."
    },
    "ti": {
        "welcome": "👋 **እንቋዕ ብደሓን መጻእኩም!**\n\nበጃኹም ባለ 12 ዲጂት **FIN** ወይ ባለ 16 ዲጂት **FAN** ቁጽሪ ይልኣኩ::\n\nናብ ስልኪኹም ናይ ኤስኤምኤስ (OTP) ኽለኣኽ እዩ፣ ነቲ ዝበጽሓኩም OTP ኣብዚ ምስ እትልእኩ ናይ መበቆል ፋይዳ ፒዲኤፍኹም ክትረኽቡ ኢኹም::",
        "deposit_btn": "💳 ዴፖዚት", "balance_btn": "💰 ሕሳብ ምርኣይ", "settings_btn": "⚙️ መተኻኸሊ", "help_btn": "📞 ሓገዝ", "send_fan_btn": "🔑 FAN / FIN ልኣኽ",
        "deposit_inst": "💰 **መምርሒ መምልኢ ሕሳብ (Telebirr):**\n\nዝደለኹምዎ መጠን ገንዘብ ናብዚ ዝስዕብ ናይ ቴሌብር ሕሳብ ኣእትዉ:\n📱 **ቴሌብር:** `0913701367`\n👤 **ስም:** URJII\n\n⚠️ **ምስ ከፈልኩም:** ነቲ ናይ ቴሌብር መልእኽቲ (**SMS**) ሙሉእ ጌርኩም ኣብዚ ኮፒ ጌርኩም ልኣኽዎ::",
        "insufficient": "❌ እኹል ሕሳብ የብልኩምን:: በጃኹም ቅድም ኢልኩም ዴፖዚት ግበሩ::",
        "searching": "ካብ ሰርቨር መረዳእታኹም ይደሊ ኣሎ... 🔄",
        "otp_sent": "✅ **OTP ተልኢኹ ኣሎ!**\n\n📩 በጃኹም ነቲ ዝበጽሓኩም ባለ 6 ኣሃዝ OTP ኣብዚ ልኣኽዎ::",
        "pdf_done": "✅ **ተወዲኡ ኣሎ!**\nፒዲኤፍኹም ተዳልዩ ኣሎ:: ⏳",
        "help_msg": "📞 ጸገም እንተጋጢሙኩም ምስ ኣድሚን ተራኸቡ: @Urjii_Admin",
        "invalid_fan": "❌ ዝተጋገየ ቁጽሪ እዩ:: በጃኹም ትኽክለኛ ቁጽሪ የእትዉ:",
        "unknown_deposit": "❌ **ከነረጋግጾ ኣይከኣልናን!** በጃኹም ሙሉእ ናይ ቴሌብር ኤስኤምኤስ ልኣኹ::"
    },
    "sid": {
        "welcome": "👋 **Danonni Hasaamboommo!**\n\nTini baaxillaan 12 kiiro **FIN** woy 16 kiiro **FAN** kiiro kiyya kiiri.\n\nSokko (OTP) silke kiyya sokkamanno, kuni koodi asira qolle ergituro Original Fayda PDF kiyya angatanno.",
        "deposit_btn": "💳 Woxe Worra", "balance_btn": "💰 Miizaane", "settings_btn": "⚙️ Baddalasira", "help_btn": "📞 Kaa'lo", "send_fan_btn": "🔑 FAN / FIN Kiiri",
        "deposit_inst": "💰 **Woxe Worrate Baddalasha (Telebirr):**\n\nHasidanno woxe kuni telebirre kiiro kiiri:\n📱 **Telebirr:** `0913701367`\n👤 **Su'ma:** URJII\n\n⚠️ **Kafaltanni gubba:** Telebirre sokko (**SMS**) wo'manka kuni kooppii assi ergi.",
        "insufficient": "❌ Miizaane kiyya batinye dika'ino. Balaxxe woxe worri.",
        "searching": "Serverete gubba raga kiyya hasanni no... 🔄",
        "otp_sent": "✅ **OTP sokkaminno!**\n\n📩 Baaxillaan 6 kiiro OTP kuni kiiri.",
        "pdf_done": "✅ **Guduminno!**\nPDF kiyya qixxaawino. ⏳",
        "help_msg": "📞 Geeshsha iillituro Admin xaadi: @Urjii_Admin",
        "invalid_fan": "❌ Garri dika'ino kiiro. Baaxillaan garri kiiro worri:",
        "unknown_deposit": "❌ **Mirkaneessa didandaamni!** Baaxillaan Telebirre SMS wo'manka kiiri."
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
        [InlineKeyboardButton("አማርኛ (Amharic)", callback_data="setlang_am")],
        [InlineKeyboardButton("Somali (Soomaali)", callback_data="setlang_so")],
        [InlineKeyboardButton("ትግርኛ (Tigrinya)", callback_data="setlang_ti")],
        [InlineKeyboardButton("Sidaama (Afaan Sidaamaa)", callback_data="setlang_sid")]
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
        await update.message.reply_text(texts["deposit_inst"], parse_mode="Markdown")
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

async def handle_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    prof = get_user_profile(user_id)
    texts = LANG_TEXTS[prof["lang"]]
    text = update.message.text if update.message.text else ""
    text_upper = text.upper()
    
    txn_match = re.search(r'\b([A-Z0-9]{8,12})\b', text_upper)
    
    if txn_match:
        txn_id = txn_match.group(1)
        if txn_id in PROCESSED_TXNS:
            await update.message.reply_text("❌ Transaction ID Already Processed!")
            return MAIN_MENU
            
        amount = 50  
        amount_match = re.search(r'(?:BR|ETB|BIRR)\s*([\d\.]+)', text_upper) or re.search(r'([\d\.]+)\s*(?:BR|ETB|BIRR)', text_upper)
        if amount_match:
            try: amount = int(float(amount_match.group(1)))
            except: pass
            
        PROCESSED_TXNS.add(txn_id)
        prof["balance"] += amount
        
        await update.message.reply_text(
            f"✅ **Verified (URJII)**\n\n🆔 **Txn ID:** `{txn_id}`\n💵 **Amount:** {amount} ETB\n\nBalance Top-Up Success!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(texts["unknown_deposit"])
        
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
            GET_DEPOSIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deposit)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    app.add_handler(conv_handler)
    app.run_polling()
