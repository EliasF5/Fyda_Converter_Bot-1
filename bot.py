import io
import os
import telebot
from telebot import types
from PIL import Image, ImageOps
from flask import Flask
import threading

# Token bot keetii fi Chat ID kee kan Admin as galchi
API_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN_HERE'  
ADMIN_CHAT_ID = 'YOUR_PERSONAL_TELEGRAM_ID_HERE' # Chat ID kee kan Elias as galchi

bot = telebot.TeleBot(API_TOKEN)

user_lang = {}             
user_balances = {}         
user_pending_payments = {}

MY_TELEBIRR = "TeleBirr (Elias Fikadu) • 0913701367"
MY_CBE = "CBE (Elias Fikadu) • 1000270143788"

MESSAGES = {
    'en': {
        'choose_lang': "🌐 <b>Choose your language</b>",
        'lang_set': "✅ Language set to English.",
        'send_id': "📥 Please send the <b>Fayda ID</b> image (containing both sides together).",
        'processing': "⚙️ Processing your ID layout... Please wait.",
        'no_credit': "⚠️ You don't have enough credits! Type /topup to recharge."
    },
    'am': {
        'choose_lang': "🌐 <b>ቋንቋዎን ይምረጡ</b>",
        'lang_set': "✅ ቋንቋው ወደ አማርኛ ተቀይሯል።",
        'send_id': "📥 እባክዎ የመታወቂያውን ፎቶ (ሁለቱንም ገጽ በአንድ ላይ የያዘውን) ይላኩ።",
        'processing': "⚙️ መታወቂያው እየተዘጋጀ ነው... እባክዎ ይጠብቁ።",
        'no_credit': "⚠️ በቂ ክሬዲት የለዎትም! ለመግዛት /topup ይፃፉ።"
    },
    'om': {
        'choose_lang': "🌐 <b>Afaan keessan filadhaa</b>",
        'lang_set': "✅ Afaan keessan gara Afaan Oromootti jijjiirameera.",
        'send_id': "📥 Maaloo suuraa <b>Fayda ID</b> keessanii (Fuula duraa fi duubaa wal bira jiru sana) ergaa.",
        'processing': "⚙️ ID keessan piriintiif ijaaramaa jira... Maaloo obsaan eegaa.",
        'no_credit': "⚠️ Kireditii gahaa hin qabdhan! Guuttachuuf /topup jedhaa."
    }
}

@bot.message_handler(commands=['start', 'language'])
def start_bot(message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 2  # Mamiin haaraan kireditii 2 qofa bilisaan argata
        
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
    bot.send_message(call.message.chat.id, MESSAGES[lang]['send_id'], parse_mode='HTML')

# --- SYSTEM TOPUP & MANUAL ADMIN VERIFICATION ---
@bot.message_handler(commands=['topup'])
def topup_menu(message):
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("7 credits — 200 ETB", callback_data="pkg_7_200"),
        types.InlineKeyboardButton("18 credits — 500 ETB", callback_data="pkg_18_500")
    )
    bot.send_message(message.chat.id, "📦 Package Kireditii bitachuu barbaaddan filadhaa:", reply_markup=markup)

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
    msg = bot.send_message(call.message.chat.id, f"💵 Maaloo <b>{pending['price']} ETB</b> gara herrega kanaan ergaa:\n• {method}\n\nErga kaffaltanii booda <b>Transaction ID</b> qofa asirratti barreessaatti nuuf ergaa.", parse_mode='HTML')
    bot.register_next_step_handler(msg, send_to_admin_verification)

def send_to_admin_verification(message):
    user_id = message.from_user.id
    tx_id = message.text.strip()
    pending = user_pending_payments.get(user_id)
    
    if not pending: return
    
    bot.send_message(message.chat.id, "⏳ <b>Kafaltiin keessan mirkanaawaa jira... Admin herrega check godhee daqiiqaa muraasa keessatti siif fe'a.</b>", parse_mode='HTML')
    
    # Gara Admin (Elias) itti erga akka ati caal jettee hin fudhanneef
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(types.InlineKeyboardButton("Mirkaneessi ✅", callback_data=f"approve_{user_id}_{pending['credits']}"))
    
    bot.send_message(ADMIN_CHAT_ID, f"🔔 <b>Kafaltii Haaraa Urjii!</b>\n\n• User ID: <code>{user_id}</code>\n• Maqaa: {message.from_user.first_name}\n• Tx ID: <code>{tx_id}</code>\n• Kireditii: {pending['credits']} (%d ETB)" % pending['price'], reply_markup=admin_markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
def admin_approve(call):
    _, user_id, credits = call.data.split('_')
    user_id = int(user_id)
    credits = int(credits)
    
    user_balances[user_id] = user_balances.get(user_id, 0) + credits
    bot.answer_callback_query(call.id, "Kireditiin mirkanaayeera!")
    bot.edit_message_text(f"✅ User {user_id} tiif Kireditii {credits} itti dabamteera.", call.message.chat.id, call.message.message_id)
    
    # Mamiif ergaa nagaa deebisuu
    bot.send_message(user_id, f"🎉 <b>Kafaltiin keessan mirkanaayeera! Kireditiin {credits} herrega keessanitti dabalameera.</b> Amma suuraa ID keessanii erguu dandeessu.", parse_mode='HTML')

# --- CORE IMAGE SPLITTING & PVC MIRRORING LAYOUT ---
@bot.message_handler(content_types=['photo'])
def handle_single_id_sheet(message):
    user_id = message.from_user.id
    lang = user_lang.get(user_id, 'om')
    
    if user_balances.get(user_id, 0) <= 0:
        bot.send_message(message.chat.id, MESSAGES[lang]['no_credit'], parse_mode='HTML')
        return

    bot.send_message(message.chat.id, MESSAGES[lang]['processing'], parse_mode='HTML')
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        full_img = Image.open(io.BytesIO(downloaded_file))
        
        W, H = full_img.size
        
        # Suuraa walitti qabamaa sana walakkaan hiree qora (Split Left & Right)
        # 1. Gala Dugdaa (Back Side) — Bitaa irra jira
        back_box = (0, 0, int(W * 0.5), int(H * 0.25)) # Hamma ID dhiphaa qora
        back_side = full_img.crop(back_box)
        
        # 2. Fuula Duraa (Front Side) — Mirga irra jira
        front_box = (int(W * 0.5), 0, W, int(H * 0.25))
        front_side = full_img.crop(front_box)
        
        # Hamma Standard PVC Kaardii (1011x638 pixels)
        card_w, card_h = 1011, 638
        front_final = front_side.resize((card_w, card_h))
        back_final = back_side.resize((card_w, card_h))
        
        # Piriintii PVC tiif dahuu (Mirroring)
        front_final = ImageOps.mirror(front_final)
        back_final = ImageOps.mirror(back_final)
        
        # Canvas Guddaa A4 (2480x3508 pixels)
        canvas = Image.new('RGB', (2480, 3508), '#FFFFFF')
        
        # Gara A4 Canvas irratti ijaaruu (Back on Left, Front on Right)
        canvas.paste(back_final, (150, 200))      
        canvas.paste(front_final, (1250, 200))    
        
        bio = io.BytesIO()
        canvas.save(bio, 'JPEG', quality=100)
        bio.seek(0)
        
        user_balances[user_id] -= 1
        bot.send_photo(message.chat.id, bio, caption=f"✅ <b>ID Keessan Sirriitti Ijaarameera!</b>\n\n• Bitaa: Gala Dugdaa (Back Side)\n• Mirga: Fuula Duraa (Front Side)\n🪞 Mirror: <b>ON (Ready for PVC Print)</b>", parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Hojiin sun hin milkoofne, maaloo irra deebii yaali. Error: {str(e)}")

app = Flask('')
@app.route('/')
def home(): return "Active"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
