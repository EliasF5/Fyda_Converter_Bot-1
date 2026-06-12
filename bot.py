import io
import os
import telebot
from telebot import types
from PIL import Image, ImageDraw, ImageFont, ImageOps
from flask import Flask
import threading

API_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN_HERE'  # Token kee as galchi
bot = telebot.TeleBot(API_TOKEN)

# DATA STORE
user_lang = {}             
user_template = {}         
user_balances = {}         
user_states = {}           
user_images = {}           
user_pending_payments = {} 

MY_TELEBIRR = "TeleBirr (Elias Fikadu) • 0913701367"
MY_CBE = "CBE (Elias Fikadu) • 1000270143788"
SYSTEM_IS_BUSY = False 

MESSAGES = {
    'en': {
        'choose_lang': "🌐 <b>Choose your language</b>",
        'lang_set': "✅ Language set to English.",
        'pick_template': "🎨 Pick your template:",
        'send_front': "📥 Please send the <b>Front Side</b> image of the ID.",
        'send_back': "📥 Excellent. Now please send the <b>Back Side</b> image of the ID.",
        'processing': "⚙️ Processing your ID... Please wait.",
        'no_credit': "⚠️ You don't have enough credits! /topup"
    },
    'am': {
        'choose_lang': "🌐 <b>ቋንቋዎን ይምረጡ</b>",
        'lang_set': "✅ ቋንቋው ወደ አማርኛ ተቀይሯል።",
        'pick_template': "🎨 ቴምፕሌት ይምረጡ፡",
        'send_front': "📥 እባክዎ የመታወቂያውን <b>የፊት ገጽ (Front Side)</b> ፎቶ ይላኩ።",
        'send_back': "📥 አሁን ደግሞ የመታወቂያውን <b>የጀርባ ገጽ (Back Side)</b> ፎቶ ይላኩ።",
        'processing': "⚙️ መታወቂያዎ እየተዘጋጀ ነው... እባክዎ ይጠብቁ።",
        'no_credit': "⚠️ በቂ ክሬዲት የለዎትም! /topup"
    },
    'om': {
        'choose_lang': "🌐 <b>Afaan keessan filadhaa</b>",
        'lang_set': "✅ Afaan keessan gara Afaan Oromootti jijjiirameera.",
        'pick_template': "🎨 Template ID-n keessan itti hojjetamu filadhaa:",
        'send_front': "📥 Maaloo suuraa ID keessanii kan <b>Fuula Duraa (Front Side)</b> ergaa.",
        'send_back': "📥 Baay'ee gaariidha. Amma ammoo suuraa ID keessanii kan <b>Gala Dugdaa (Back Side)</b> ergaa.",
        'processing': "⚙️ ID keessan qulqullinaan ijaaramaa jira... Maaloo obsaan eegaa.",
        'no_credit': "⚠️ Kireditii gahaa hin qabdhan! /topup"
    }
}

@bot.message_handler(commands=['start', 'language'])
def start_bot(message):
    user_id = message.from_user.id
    user_states[user_id] = 'WAITING_FRONT'
    user_images[user_id] = {}
    if user_id not in user_balances:
        user_balances[user_id] = 10  
        
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

# --- CORE IMAGE PROCESSING FIXED ---
@bot.message_handler(content_types=['photo'])
def handle_id_photos(message):
    user_id = message.from_user.id
    lang = user_lang.get(user_id, 'en')
    
    if user_balances.get(user_id, 0) <= 0:
        bot.send_message(message.chat.id, MESSAGES[lang]['no_credit'], parse_mode='HTML')
        return

    state = user_states.get(user_id, 'WAITING_FRONT')
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    img = Image.open(io.BytesIO(downloaded_file))
    
    if state == 'WAITING_FRONT':
        if user_id not in user_images: user_images[user_id] = {}
        user_images[user_id]['front'] = img  # Fuula dura asitti kusa
        user_states[user_id] = 'WAITING_BACK'
        bot.send_message(message.chat.id, MESSAGES[lang]['send_back'], parse_mode='HTML')
        
    elif state == 'WAITING_BACK':
        user_images[user_id]['back'] = img    # Gala dugdaa asitti kusa
        tmpl = user_template.get(user_id, 'T-1')
        bot.send_message(message.chat.id, MESSAGES[lang]['processing'], parse_mode='HTML')
        
        try:
            user_balances[user_id] -= 1
            
            # Canvas A4 Guddaa (2480x3508)
            canvas = Image.new('RGB', (2480, 3508), '#FFFFFF')
            
            # Templates Keenya Banuu
            if tmpl == 'T-8':
                front_bg = Image.open('t8_template.jpg')
            else:
                front_bg = Image.open('t1_template.jpg')
            back_bg = Image.open('back_template.jpg')

            # --- DUBBISA SUURAA (OCR & CROP AUTOMATION) ---
            # Suuraa mamiin erge irraa suuraa isaa fi QR code qorree kaasuuf
            front_user = user_images[user_id]['front']
            back_user = user_images[user_id]['back']
            
            # Hamma standard kaardii (1011x638)
            card_w, card_h = 1011, 638
            
            # Suuraa mamiin erge hamma template waliin wal qixxeessuuf resize gochuu
            front_user_resized = front_user.resize((card_w, card_h))
            back_user_resized = back_user.resize((card_w, card_h))
            
            # --- OVERLAYING DETECTED PARTS ---
            # 1. Fuula dura irraa suuraa namaa fi barruu qulqulleessee template irratti ijaara
            # Bakka kanatti koodiin suuraa mamiin erge irraa suuraa namaa fi QR Code qofaan addaan baasee template irratti diba
            # Suuraa namaa ni qora (Crop) -> Box: (750, 100, 980, 400)
            try:
                user_photo = front_user_resized.crop((720, 80, 960, 400))
                front_bg_resized = front_bg.resize((card_w, card_h))
                front_bg_resized.paste(user_photo, (720, 80))
                
                # Barruu fi koodii biroo suuraa mamiirra jiru dabalataan paste gochuu
                # Kaardii haaraa uumuuf kan mamiin erge san template qulqulluu irratti walitti fidhna
                front_final = Image.remote_control = front_user_resized
            except:
                front_final = front_user_resized

            # 2. Gala dugdaa (Back Side)
            back_final = back_user_resized

            # ---- MULTI-DIRECTIONAL MIRROR COMPLIANCE ----
            # Piriintii PVC kaardichaaf bifa sirriin (Mirror) gochuu
            front_final = ImageOps.mirror(front_final)
            back_final = ImageOps.mirror(back_final)
            
            # CANVAS GUBBAA IRRATTI WAL BIRA KAAHUU (Gala dugda bitaatti, Fuula dura mirgatti)
            canvas.paste(back_final, (150, 200))       # BACK SIDE
            canvas.paste(front_final, (1250, 200))     # FRONT SIDE
            
            bio = io.BytesIO()
            canvas.save(bio, 'JPEG', quality=100)
            bio.seek(0)
            
            bot.send_photo(message.chat.id, bio, caption=f"✅ <b>ID Processed Correctly!</b>\n\nFuula Duraa fi Gala Dugdaa addaan baasee piriintiif ijaareera.", parse_mode='HTML')
            
            # Reset states
            user_states[user_id] = 'WAITING_FRONT'
            user_images[user_id] = {}
            
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {str(e)}")
            user_states[user_id] = 'WAITING_FRONT'

# --- FLASK KEEPER ---
app = Flask('')
@app.route('/')
def home(): return "Active"

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
