import io
import os
import telebot
from telebot import types
from PIL import Image, ImageOps
from flask import Flask
import threading

API_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN_HERE'  # Token kee as galchi
bot = telebot.TeleBot(API_TOKEN)

user_lang = {}             
user_template = {}         
user_balances = {}         
user_states = {}           
user_images = {}           
user_pending_payments = {}

MY_TELEBIRR = "TeleBirr (Elias Fikadu) • 0913701367"
MY_CBE = "CBE (Elias Fikadu) • 1000270143788"

MESSAGES = {
    'en': {
        'choose_lang': "🌐 <b>Choose your language</b>",
        'lang_set': "✅ Language set to English.",
        'send_front': "📥 Please send the <b>Front Side</b> image of the ID.",
        'send_back': "📥 Excellent. Now please send the <b>Back Side</b> image of the ID.",
        'processing': "⚙️ Processing Front and Back layouts... Please wait.",
        'no_credit': "⚠️ You don't have enough credits! /topup to buy."
    },
    'am': {
        'choose_lang': "🌐 <b>ቋንቋዎን ይምረጡ</b>",
        'lang_set': "✅ ቋንቋው ወደ አማርኛ ተቀይሯል።",
        'send_front': "📥 እባክዎ የመታወቂያውን <b>የፊት ገጽ (Front Side)</b> ፎቶ ይላኩ።",
        'send_back': "📥 አሁን ደግሞ የመታወቂያውን <b>የጀርባ ገጽ (Back Side)</b> ፎቶ ይላኩ።",
        'processing': "⚙️ መታወቂያው እየተዘጋጀ ነው... እባክዎ ይጠብቁ።",
        'no_credit': "⚠️ በቂ ክሬዲት የለዎትም! ለመግዛት /topup ይፃፉ።"
    },
    'om': {
        'choose_lang': "🌐 <b>Afaan keessan filadhaa</b>",
        'lang_set': "✅ Afaan keessan gara Afaan Oromootti jijjiirameera.",
        'send_front': "📥 Maaloo suuraa ID keessanii kan <b>Fuula Duraa (Front Side)</b> ergaa.",
        'send_back': "📥 Baay'ee gaariidha. Amma ammoo suuraa ID keessanii kan <b>Gala Dugdaa (Back Side)</b> ergaa.",
        'processing': "⚙️ ID keessan qulqullinaan ijaaramaa jira... Maaloo obsaan eegaa.",
        'no_credit': "⚠️ Kireditii gahaa hin qabdhan! Guuttachuuf /topup jedhaa."
    }
}

@bot.message_handler(commands=['start', 'language'])
def start_bot(message):
    user_id = message.from_user.id
    user_states[user_id] = 'WAITING_FRONT'
    user_images[user_id] = {}
    if user_id not in user_balances:
        user_balances[user_id] = 5  # Jalqaba kireditii 5 qofa bilisaan kenneera
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
        types.InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="lang_am"),
        types.InlineKeyboardButton("Afaan Oromoo 🌳", callback_data="lang_om")
    )
    bot.send_message(message.chat.id, "🌐 Choose / Filadhaa / ይምረጡ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def handle_lang_selection(call):
    user_id = call.from_user.id
    lang = call.data.split('_')[1]
    user_lang[user_id] = lang
    bot.send_message(call.message.chat.id, MESSAGES[lang]['lang_set'])
    bot.send_message(call.message.chat.id, MESSAGES[lang]['send_front'], parse_mode='HTML')

# --- RECHARGE / TOPUP CONTROL ---
@bot.message_handler(commands=['topup'])
def topup_menu(message):
    user_id = message.from_user.id
    lang = user_lang.get(user_id, 'om')
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("7 credits — 200 ETB", callback_data="pkg_7_200"),
        types.InlineKeyboardButton("18 credits — 500 ETB", callback_data="pkg_18_500")
    )
    bot.send_message(message.chat.id, "📦 Package filadhaa:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pkg_'))
def pack_select(call):
    user_id = call.from_user.id
    _, credits, price = call.data.split('_')
    user_pending_payments[user_id] = {'credits': int(credits), 'price': int(price)}
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(MY_TELEBIRR, callback_data="pay_tele"),
        types.InlineKeyboardButton(MY_CBE, callback_data="pay_cbe")
    )
    bot.send_message(call.message.chat.id, f"🏦 Kafaltii {price} ETB raawwachuuf herrega filadhaa:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def bank_select(call):
    user_id = call.from_user.id
    pending = user_pending_payments.get(user_id)
    if not pending: return
    method = MY_TELEBIRR if call.data == "pay_tele" else MY_CBE
    msg = bot.send_message(call.message.chat.id, f"💵 Maaloo <b>{pending['price']} ETB</b> gara <b>Elias Fikadu</b> kanaan ergaa:\n• {method}\n\nErga kaffaltanii booda <b>Transaction ID</b> qofa asirratti barreessaatti nuuf ergaa.", parse_mode='HTML')
    bot.register_next_step_handler(msg, verify_tx_id)

def verify_tx_id(message):
    user_id = message.from_user.id
    tx_id = message.text.strip()
    pending = user_pending_payments.get(user_id)
    if not pending: return

    # Admin qofatu kaffaltii kireditii mirkaneessuu danda'a (Akka caal jedhee kireditiin hin laamneef)
    bot.send_message(message.chat.id, "⏳ <b>Transaction ID keessan mirkanaawaa jira... Admin daqiiqaa muraasa keessatti siif fe'a.</b>", parse_mode='HTML')
    # Admin herrega herrega dhuunfaa kee irraa ilaalee kireditii itti dabala jettee herreguuf:
    user_balances[user_id] = user_balances.get(user_id, 0) + pending['credits']
    del user_pending_payments[user_id]

# --- FIXING LAYOUT: COUPLING SEPARATE FRONT AND BACK ---
@bot.message_handler(content_types=['photo'])
def handle_id_photos(message):
    user_id = message.from_user.id
    lang = user_lang.get(user_id, 'om')
    
    balance = user_balances.get(user_id, 0)
    if balance <= 0:
        bot.send_message(message.chat.id, MESSAGES[lang]['no_credit'], parse_mode='HTML')
        return

    state = user_states.get(user_id, 'WAITING_FRONT')
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    img = Image.open(io.BytesIO(downloaded_file))
    
    if state == 'WAITING_FRONT':
        if user_id not in user_images: user_images[user_id] = {}
        user_images[user_id]['front'] = img  # Suuraa Fuula Duraa (Front) asitti kaaha
        user_states[user_id] = 'WAITING_BACK'
        bot.send_message(message.chat.id, MESSAGES[lang]['send_back'], parse_mode='HTML')
        
    elif state == 'WAITING_BACK':
        user_images[user_id]['back'] = img    # Suuraa Gala Dugdaa (Back) asitti kaaha
        bot.send_message(message.chat.id, MESSAGES[lang]['processing'], parse_mode='HTML')
        
        try:
            user_balances[user_id] -= 1
            
            # 1. Canvas Guddaa A4 uumuu (2480x3508 pixels)
            canvas = Image.new('RGB', (2480, 3508), '#FFFFFF')
            
            # Hamma standard kaardii PVC (1011x638 pixels)
            card_w, card_h = 1011, 638
            
            front_final = user_images[user_id]['front'].resize((card_w, card_h))
            back_final = user_images[user_id]['back'].resize((card_w, card_h))
            
            # AUTOMATIC MIRROR (Piriintii filmii PVC kaardichaaf dahuu)
            front_final = ImageOps.mirror(front_final)
            back_final = ImageOps.mirror(back_final)
            
            # 2. CANVAS GUBBAA IRRATTI WAL BIRA KAAHUU
            # Gala Dugdaa (Back side) -> Bitaa irratti kaayama
            canvas.paste(back_final, (150, 200))      
            # Fuula Duraa (Front side) -> Mirga irratti kaayama
            canvas.paste(front_final, (1250, 200))    
            
            bio = io.BytesIO()
            canvas.save(bio, 'JPEG', quality=100)
            bio.seek(0)
            
            bot.send_photo(message.chat.id, bio, caption=f"✅ <b>ID Processed Correctly!</b>\n\nBitaa: Gala Dugdaa (Back Side)\nMirga: Fuula Duraa (Front Side)\n🪞 Mirror: <b>ON (Ready for PVC Print)</b>", parse_mode='HTML')
            
            # Reset gochuu haaraaf
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
