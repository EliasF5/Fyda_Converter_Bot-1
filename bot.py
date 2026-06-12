import io
import os
import telebot
from telebot import types
from PIL import Image, ImageDraw, ImageFont, ImageOps
from flask import Flask
import threading

API_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN_HERE'  # Token kee as galchi
bot = telebot.TeleBot(API_TOKEN)

user_lang = {}             
user_template = {}         
user_balances = {}         
user_states = {}           
user_images = {}           

MESSAGES = {
    'en': {
        'choose_lang': "🌐 <b>Choose your language</b>",
        'lang_set': "✅ Language set to English.",
        'pick_template': "🎨 Pick your template:",
        'send_front': "📥 Please send the <b>Front Side</b> image of the ID.",
        'send_back': "📥 Excellent. Now please send the <b>Back Side</b> image of the ID.",
        'processing': "⚙️ Processing your ID layouts... Please wait.",
        'no_credit': "⚠️ You don't have enough credits!"
    },
    'am': {
        'choose_lang': "🌐 <b>ቋንቋዎን ይምረጡ</b>",
        'lang_set': "✅ ቋንቋው ወደ አማርኛ ተቀይሯል።",
        'pick_template': "🎨 ቴምፕሌት ይምረጡ፡",
        'send_front': "📥 እባክዎ የመታወቂያውን <b>የፊት ገጽ (Front Side)</b> ፎቶ ይላኩ።",
        'send_back': "📥 አሁን ደግሞ የመታወቂያውን <b>የጀርባ ገጽ (Back Side)</b> ፎቶ ይላኩ።",
        'processing': "⚙️ መታወቂያው እየተነበበ ነው... እባክዎ ይጠብቁ።",
        'no_credit': "⚠️ በቂ ክሬዲት የለዎትም!"
    },
    'om': {
        'choose_lang': "🌐 <b>Afaan keessan filadhaa</b>",
        'lang_set': "✅ Afaan keessan gara Afaan Oromootti jijjiirameera.",
        'pick_template': "🎨 Template ID-n keessan itti hojjetamu filadhaa:",
        'send_front': "📥 Maaloo suuraa ID keessanii kan <b>Fuula Duraa (Front Side)</b> ergaa.",
        'send_back': "📥 Baay'ee gaariidha. Amma ammoo suuraa ID keessanii kan <b>Gala Dugdaa (Back Side)</b> ergaa.",
        'processing': "⚙️ ID keessan qulqullinaan sassaabamaa jira... Maaloo obsaan eegaa.",
        'no_credit': "⚠️ Kireditii gahaa hin qabdhan!"
    }
}

@bot.message_handler(commands=['start', 'language'])
def start_bot(message):
    user_id = message.from_user.id
    user_states[user_id] = 'WAITING_FRONT'
    user_images[user_id] = {}
    if user_id not in user_balances:
        user_balances[user_id] = 100  
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
        types.InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="lang_am"),
        types.InlineKeyboardButton("Afaan Oromoo 🌳", callback_data="lang_om")
    )
    bot.send_message(message.chat.id, MESSAGES['om']['choose_lang'], reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def handle_lang_selection(call):
    user_id = call.from_user.id
    lang = call.data.split('_')[1]
    user_lang[user_id] = lang
    bot.send_message(call.message.chat.id, MESSAGES[lang]['lang_set'])
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎨 T-1 Small shadow", callback_data="tmpl_T-1"),
        types.InlineKeyboardButton("🎨 T-8 White rectangle", callback_data="tmpl_T-8")
    )
    bot.send_message(call.message.chat.id, MESSAGES[lang]['pick_template'], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('tmpl_'))
def handle_template_selection(call):
    user_id = call.from_user.id
    lang = user_lang.get(user_id, 'en')
    user_template[user_id] = call.data.split('_')[1]
    bot.send_message(call.message.chat.id, MESSAGES[lang]['send_front'], parse_mode='HTML')

@bot.message_handler(content_types=['photo'])
def handle_id_photos(message):
    user_id = message.from_user.id
    lang = user_lang.get(user_id, 'en')
    
    state = user_states.get(user_id, 'WAITING_FRONT')
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    img = Image.open(io.BytesIO(downloaded_file)).convert('RGBA')
    
    if state == 'WAITING_FRONT':
        user_images[user_id]['front'] = img
        user_states[user_id] = 'WAITING_BACK'
        bot.send_message(message.chat.id, MESSAGES[lang]['send_back'], parse_mode='HTML')
        
    elif state == 'WAITING_BACK':
        user_images[user_id]['back'] = img
        tmpl = user_template.get(user_id, 'T-1')
        bot.send_message(message.chat.id, MESSAGES[lang]['processing'], parse_mode='HTML')
        
        try:
            # 1. Canvas Guddaa A4 (2480x3508 pixels)
            canvas = Image.new('RGB', (2480, 3508), '#FFFFFF')
            
            # Templates Keenya Banuu (Bifa RGBA n)
            if tmpl == 'T-8':
                front_template = Image.open('t8_template.jpg').convert('RGBA')
            else:
                front_template = Image.open('t1_template.jpg').convert('RGBA')
            back_template = Image.open('back_template.jpg').convert('RGBA')

            card_w, card_h = 1011, 638
            front_template = front_template.resize((card_w, card_h))
            back_template = back_template.resize((card_w, card_h))

            # Suuraalee mamiin erge gosa standard kaardichaatti resize gochuu
            front_user = user_images[user_id]['front'].resize((card_w, card_h))
            back_user = user_images[user_id]['back'].resize((card_w, card_h))

            # ----------------------------------------------------
            # 2. FUULA DURAA IJAARUU (Extracting User Details)
            # ----------------------------------------------------
            # Suuraa mamiirraa Barruu, Suuraa dhuunfaa fi Barcode qorree baasna
            # Suuraa namaa (Crop photo)
            user_face = front_user.crop((780, 150, 970, 390))
            # Suuraa xiqqaa (Mini photo)
            user_mini_face = front_user.crop((550, 440, 615, 520))
            # Barruu ragaalee (Text area crop)
            user_info_text = front_user.crop((400, 140, 780, 430))
            # Barcode (Gara gadii)
            user_barcode = front_user.crop((620, 430, 760, 480))
            
            # Amma templates haaraa qulqulluu irratti bakka isaanii eegnee suufna
            front_layout = front_template.copy()
            front_layout.paste(user_face, (780, 150))
            front_layout.paste(user_mini_face, (550, 440))
            front_layout.paste(user_info_text, (400, 140), user_info_text if user_info_text.mode == 'RGBA' else None)
            front_layout.paste(user_barcode, (620, 430))

            # ----------------------------------------------------
            # 3. GALA DUGDAA IJAARUU (Extracting Back Details)
            # ----------------------------------------------------
            # QR Code fi barruu dugda irraa qorra
            user_qr = back_user.crop((60, 40, 290, 410))
            user_back_text = back_user.crop((295, 40, 470, 410))
            
            back_layout = back_template.copy()
            back_layout.paste(user_qr, (60, 40))
            back_layout.paste(user_back_text, (295, 40))

            # ----------------------------------------------------
            # 4. MIRROR & LAYOUT COUPLING
            # ----------------------------------------------------
            # Gosa RGBA gara RGB tti jijjiiruuf (Jifniidhnaan piriintiif)
            front_final = front_layout.convert('RGB')
            back_final = back_layout.convert('RGB')

            # Hojii PVC printii kaardichaaf (Mirroring)
            front_final = ImageOps.mirror(front_final)
            back_final = ImageOps.mirror(back_final)
            
            # Layout alignment on A4 Canvas (Back side on Left, Front side on Right)
            canvas.paste(back_final, (150, 200))      
            canvas.paste(front_final, (1250, 200))    
            
            bio = io.BytesIO()
            canvas.save(bio, 'JPEG', quality=100)
            bio.seek(0)
            
            bot.send_photo(message.chat.id, bio, caption=f"✅ <b>ID Keessan Sirriitti Ijaarameera!</b>\n🎨 Template: {tmpl}\n🪞 Mirror: <b>ON (Ready for PVC Print)</b>", parse_mode='HTML')
            
            user_states[user_id] = 'WAITING_FRONT'
            user_images[user_id] = {}
            
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {str(e)}")
            user_states[user_id] = 'WAITING_FRONT'

app = Flask('')
@app.route('/')
def home(): return "Active"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
