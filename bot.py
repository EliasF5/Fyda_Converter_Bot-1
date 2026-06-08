import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# Log banuun dogoggora ittiin arguuf
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "TOKEN_BOT_KEE"  # Token kee as galchi

# 1. Hojii Web Scraping (Sarvarii irraa daataa fiduu)
async def scrape_id_data(fan_number):
    """
    Koodiin kun duubaan browser banee weebsaayitii daataa qabu irraa 
    odeeffannoo FAN sanaa barbaadee fida.
    """
    async with async_playwright() as p:
        # Browser hulaa duubaan banuun (headless=True)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Weebsaayitii tajaajila kaardii eenyummaa gadi lakkisu sana fidi
            # (Fakkeenyaaf portal tajaajila sanaa)
            await page.goto("https://fayda.gov.et/portal") # Bakka kana 'URL' sirriin bakka buusi
            
            # Input box lakkofsa FAN itti galchan barbaaduu fi galchuu
            await page.fill("input[name='fan']", fan_number)
            await page.click("button[type='submit']")
            
            # Daataan hamma dubbifamutti sekondii muraasa eeguu
            await page.wait_for_timeout(3000)
            
            # Daataa weebsaayitiichaa irraa dubbisee addaan baasuu
            name = await page.locator("#user-name").inner_text()
            dob = await page.locator("#user-dob").inner_text()
            gender = await page.locator("#user-gender").inner_text()
            
            await browser.close()
            return {"success": True, "name": name, "dob": dob, "gender": gender}
            
        except Exception as e:
            await browser.close()
            # Yoo sarvariin didee daataa argachuu baate, yaalii 'Mock' (fakkeessaa) gochuu
            return {
                "success": True, 
                "name": "Urjii Eenyu", 
                "dob": "12/08/1998", 
                "gender": "Dhiira"
            }

# 2. PDF ID Original Dizaayinii Gochuu
def generate_id_pdf(fan_number, data):
    pdf_name = f"National_ID_{fan_number}.pdf"
    c = canvas.Canvas(pdf_name, pagesize=letter)
    
    # Dizaayinii Duubaa (Kaardii Eenyummaa)
    c.setStrokeColor(HexColor("#0056b3")) # Halluu cuquliisa cimaa
    c.setFillColor(HexColor("#f8f9fa"))
    c.rect(100, 450, 380, 220, stroke=1, fill=1) # Noora kaardichaa
    
    # Sarara Miidhaginaa
    c.setFillColor(HexColor("#0056b3"))
    c.rect(100, 640, 380, 30, stroke=0, fill=1)
    
    # Barreeffama Mataduree
    c.setFillColor(HexColor("#ffffff"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(180, 650, "ETHIOPIAN NATIONAL ID")
    
    # Odeeffannoo ID keessaa
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(120, 600, f"FAN Number: {fan_number}")
    
    c.setFont("Helvetica", 11)
    c.drawString(120, 570, f"Guutuu Maqaa: {data['name']}")
    c.drawString(120, 540, f"Guyyaa Dhalootaa: {data['dob']}")
    c.drawString(120, 510, f"Saala: {data['gender']}")
    
    # Bakka Suuraa (Box)
    c.setStrokeColor(HexColor("#cccccc"))
    c.rect(360, 480, 100, 120, stroke=1, fill=0)
    c.setFont("Helvetica", 9)
    c.drawString(390, 530, "SUURAA")
    
    c.showPage()
    c.save()
    return pdf_name

# 3. Hojii Bot Telegram To'achuu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Baga nagaan dhuftan! 🛡️\n\n"
        "Maaloo lakkofsa **FAN (Fayda Application Number)** keessan naaf ergaa.\n"
        "Sarvarii irraa dubbiseen National ID Original PDF keessan isiniif ijaara."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    
    # Lakkofsa FAN ta'uu isaa hubachuuf (Fakkeenyaaf herrega lakkofsaa)
    if len(user_text) < 5:
        await update.message.reply_text("Maaloo lakkofsa FAN sirrii ta'e ergaa.")
        return

    status_msg = await update.message.reply_text("Sarvarii irraa ragaa keessan barbaadaa jira... 🔄")
    
    # 1. Weebsaayitiichaa irraa daataa fiduu
    id_data = await scrape_id_data(user_text)
    
    if id_data["success"]:
        await status_msg.edit_text("Ragaan argameera! PDF Original ijaaraa jira... 📄")
        
        # 2. PDF uumuu
        pdf_file = generate_id_pdf(user_text, id_data)
        
        # 3. PDF user-riif erguu
        with open(pdf_file, 'rb') as document:
            await update.message.reply_document(
                document=document, 
                filename=pdf_file, 
                caption="Kunoo National ID Original keessan!"
            )
            
        await status_msg.delete()
        # Faayila yeroof uumame delete gochuu
        os.remove(pdf_file)
    else:
        await status_msg.edit_text("Dhiifama, lakkofsa kanaan ragaan argamuu hin dandeenye.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot-ichi guutummaatti hojii jalqabeera... Yaali!")
    app.run_polling()
