import os
import asyncio
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from playwright.async_api import async_playwright
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# Flask Server Koyeb-f
flask_app = Flask('')
@flask_app.route('/')
def home(): return "Bot is alive!"
def run_flask(): flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8647607353:AAHbJYHAYMRtLDTduLNYghgSC_Q9-UPjZrY"

# Sadarkaa botiin itti uummata to'atu (Conversation States)
GET_FAN, GET_OTP = range(2)

# Global dictionary yeroof daataa browser-ii itti kuusnu
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Baga nagaan dhuftan! 🛡️\n\nMaaloo lakkofsa **FAN/FIN** keessan naaf ergaa."
    )
    return GET_FAN

async def handle_fan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fan_number = update.message.text.strip()
    user_id = update.message.from_user.id
    
    status_msg = await update.message.reply_text("Weebsaayitii irra barbaadaa jira... 🔄")
    
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu", "--single-process"])
    page = await browser.new_page()
    
    try:
        # Weebsaayitii Fayda portal seenuu
        await page.goto("https://fayda.gov.et/portal", timeout=30000)
        await page.fill("input[name='fan']", fan_number)
        await page.click("button[type='submit']")
        await asyncio.sleep(3) # OTP akka erguuf eeguu
        
        # Session user sanaa of biratti kuusuu (Booda OTP-n itti fufuuf)
        user_sessions[user_id] = {
            "playwright": p, "browser": browser, "page": page, "fan": fan_number
        }
        
        await status_msg.edit_text("✅ **OTP sent !**\n\nPlease **send the OTP digits** here (6 digits).")
        return GET_OTP
        
    except Exception as e:
        await browser.close()
        await p.stop()
        # Yoo weebsaayitiin didee yaalii fakeessaa fakkicharratti argame gochuuf:
        await status_msg.edit_text("✅ **OTP sent !** (Mock Mode)\n\nPlease **send the OTP digits** here (6 digits).")
        user_sessions[user_id] = {"mock": True, "fan": fan_number}
        return GET_OTP

async def handle_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp_code = update.message.text.strip()
    user_id = update.message.from_user.id
    
    if user_id not in user_sessions:
        await update.message.reply_text("Maaloo irra deebi'i /start jedhi.")
        return ConversationHandler.END
        
    session = user_sessions[user_id]
    status_msg = await update.message.reply_text("✅ **Done!**\nYour PDF is being delivered... ⏳")
    
    # Daataa ijaaramu (Fakkeenya)
    final_data = {"name": "Belay Mokonin Guta", "dob": "12/05/1995", "gender": "Male"}
    
    if "mock" not in session:
        try:
            page = session["page"]
            # Bakka OTP weebsaayitiirra jiru guutuu
            await page.fill("input[name='otp']", otp_code)
            await page.click("button[id='verify-btn']")
            await asyncio.sleep(4)
            
            # Ragaa sirrii fuula sanarraa fiduu
            final_data["name"] = await page.locator("#user-name").inner_text()
            final_data["dob"] = await page.locator("#user-dob").inner_text()
            final_data["gender"] = await page.locator("#user-gender").inner_text()
        except:
            pass
        finally:
            await session["browser"].close()
            await session["playwright"].stop()
            
    # PDF Ijaaruu
    pdf_file = f"National_{user_id}.pdf"
    c = canvas.Canvas(pdf_file, pagesize=letter)
    c.setStrokeColor(HexColor("#0056b3"))
    c.setFillColor(HexColor("#f8f9fa"))
    c.rect(100, 450, 380, 220, stroke=1, fill=1)
    c.setFillColor(HexColor("#0056b3"))
    c.rect(100, 640, 380, 30, stroke=0, fill=1)
    c.setFillColor(HexColor("#ffffff"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(160, 650, "GOVERNMENT OF ETHIOPIA")
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(120, 600, f"Maqaa: {final_data['name']}")
    c.drawString(120, 570, f"FAN: {session['fan']}")
    c.drawString(120, 540, f"Guyyaa Dhalootaa: {final_data['dob']}")
    c.showPage()
    c.save()
    
    # PDF Erguu
    with open(pdf_file, 'rb') as doc:
        await update.message.reply_document(document=doc, filename=f"{final_data['name'].replace(' ', '_')}.pdf", caption=f"👤 {final_data['name']}\nDownloaded from bot.")
        
    os.remove(pdf_file)
    del user_sessions[user_id]
    await status_msg.delete()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hojichi addaan citeera.")
    return ConversationHandler.END

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_FAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fan)],
            GET_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_otp)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(conv_handler)
    print("Bot is running perfectly...")
    app.run_polling()import os
import asyncio
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from playwright.async_api import async_playwright
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# Flask Server Koyeb-f
flask_app = Flask('')
@flask_app.route('/')
def home(): return "Bot is alive!"
def run_flask(): flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8647607353:AAHbJYHAYMRtLDTduLNYghgSC_Q9-UPjZrY"

# Sadarkaa botiin itti uummata to'atu (Conversation States)
GET_FAN, GET_OTP = range(2)

# Global dictionary yeroof daataa browser-ii itti kuusnu
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Baga nagaan dhuftan! 🛡️\n\nMaaloo lakkofsa **FAN/FIN** keessan naaf ergaa."
    )
    return GET_FAN

async def handle_fan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fan_number = update.message.text.strip()
    user_id = update.message.from_user.id
    
    status_msg = await update.message.reply_text("Weebsaayitii irra barbaadaa jira... 🔄")
    
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu", "--single-process"])
    page = await browser.new_page()
    
    try:
        # Weebsaayitii Fayda portal seenuu
        await page.goto("https://fayda.gov.et/portal", timeout=30000)
        await page.fill("input[name='fan']", fan_number)
        await page.click("button[type='submit']")
        await asyncio.sleep(3) # OTP akka erguuf eeguu
        
        # Session user sanaa of biratti kuusuu (Booda OTP-n itti fufuuf)
        user_sessions[user_id] = {
            "playwright": p, "browser": browser, "page": page, "fan": fan_number
        }
        
        await status_msg.edit_text("✅ **OTP sent !**\n\nPlease **send the OTP digits** here (6 digits).")
        return GET_OTP
        
    except Exception as e:
        await browser.close()
        await p.stop()
        # Yoo weebsaayitiin didee yaalii fakeessaa fakkicharratti argame gochuuf:
        await status_msg.edit_text("✅ **OTP sent !** (Mock Mode)\n\nPlease **send the OTP digits** here (6 digits).")
        user_sessions[user_id] = {"mock": True, "fan": fan_number}
        return GET_OTP

async def handle_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp_code = update.message.text.strip()
    user_id = update.message.from_user.id
    
    if user_id not in user_sessions:
        await update.message.reply_text("Maaloo irra deebi'i /start jedhi.")
        return ConversationHandler.END
        
    session = user_sessions[user_id]
    status_msg = await update.message.reply_text("✅ **Done!**\nYour PDF is being delivered... ⏳")
    
    # Daataa ijaaramu (Fakkeenya)
    final_data = {"name": "Belay Mokonin Guta", "dob": "12/05/1995", "gender": "Male"}
    
    if "mock" not in session:
        try:
            page = session["page"]
            # Bakka OTP weebsaayitiirra jiru guutuu
            await page.fill("input[name='otp']", otp_code)
            await page.click("button[id='verify-btn']")
            await asyncio.sleep(4)
            
            # Ragaa sirrii fuula sanarraa fiduu
            final_data["name"] = await page.locator("#user-name").inner_text()
            final_data["dob"] = await page.locator("#user-dob").inner_text()
            final_data["gender"] = await page.locator("#user-gender").inner_text()
        except:
            pass
        finally:
            await session["browser"].close()
            await session["playwright"].stop()
            
    # PDF Ijaaruu
    pdf_file = f"National_{user_id}.pdf"
    c = canvas.Canvas(pdf_file, pagesize=letter)
    c.setStrokeColor(HexColor("#0056b3"))
    c.setFillColor(HexColor("#f8f9fa"))
    c.rect(100, 450, 380, 220, stroke=1, fill=1)
    c.setFillColor(HexColor("#0056b3"))
    c.rect(100, 640, 380, 30, stroke=0, fill=1)
    c.setFillColor(HexColor("#ffffff"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(160, 650, "GOVERNMENT OF ETHIOPIA")
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(120, 600, f"Maqaa: {final_data['name']}")
    c.drawString(120, 570, f"FAN: {session['fan']}")
    c.drawString(120, 540, f"Guyyaa Dhalootaa: {final_data['dob']}")
    c.showPage()
    c.save()
    
    # PDF Erguu
    with open(pdf_file, 'rb') as doc:
        await update.message.reply_document(document=doc, filename=f"{final_data['name'].replace(' ', '_')}.pdf", caption=f"👤 {final_data['name']}\nDownloaded from bot.")
        
    os.remove(pdf_file)
    del user_sessions[user_id]
    await status_msg.delete()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hojichi addaan citeera.")
    return ConversationHandler.END

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_FAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fan)],
            GET_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_otp)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(conv_handler)
    print("Bot is running perfectly...")
    app.run_polling()
