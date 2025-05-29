import telebot from telebot import types import json import os from flask import Flask, request from datetime import datetime

==== CONFIG ====

TOKEN = '7812379714:AAHeBy8IFoFZ60B8KRNIriSuDRYf_VlRVPs' ADMIN_ID = 7864621105 WEBHOOK_URL = f"https://telegram-botim.onrender.com/{TOKEN}"

bot = telebot.TeleBot(TOKEN) server = Flask(name)

==== CATEGORIES ====

CATEGORIES = [ "Beton asboblari", "Elektr asboblar", "Qurilish materiallari", "O'lchov uskunalari", "Himoya vositalari", "Yelim va bo'yoqlar", "Metall asboblar", "Santexnika buyumlari", "Payvandlash jihozlari", "Bog' asboblari" ]

==== PRODUCT STORAGE ====

PRODUCTS_FILE = 'data/products.json' os.makedirs('data', exist_ok=True) if not os.path.exists(PRODUCTS_FILE): with open(PRODUCTS_FILE, 'w') as f: json.dump([], f)

==== LOAD PRODUCTS ====

def load_products(): with open(PRODUCTS_FILE, 'r') as f: return json.load(f)

def save_product(product): products = load_products() products.append(product) with open(PRODUCTS_FILE, 'w') as f: json.dump(products, f, indent=2)

==== START ====

@bot.message_handler(commands=['start']) def send_welcome(message): markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2) for cat in CATEGORIES: markup.add(types.KeyboardButton(cat)) bot.send_message(message.chat.id, "🏗 Mahsulotlar toifasini tanlang:", reply_markup=markup)

==== CATEGORY SELECT ====

@bot.message_handler(func=lambda message: message.text in CATEGORIES) def show_products_by_category(message): cat = message.text products = [p for p in load_products() if p['category'] == cat] if not products: bot.send_message(message.chat.id, "❌ Bu toifada mahsulot yo'q.") return for p in products: text = f"🛠 <b>{p['name']}</b>\n💵 Narxi: {p['price']} so'm\n🆔 ID: {p['id']}" bot.send_photo(message.chat.id, p['image'], caption=text, parse_mode='HTML')

==== ADMIN PANEL ====

@bot.message_handler(commands=['admin']) def admin_panel(message): if message.from_user.id != ADMIN_ID: return markup = types.ReplyKeyboardMarkup(resize_keyboard=True) markup.add("➕ Mahsulot qo‘shish") bot.send_message(message.chat.id, "🔐 Admin paneliga xush kelibsiz!", reply_markup=markup)

==== ADD PRODUCT ====

admin_states = {}

@bot.message_handler(func=lambda m: m.text == "➕ Mahsulot qo‘shish") def ask_product_name(message): if message.from_user.id != ADMIN_ID: return admin_states[message.chat.id] = {'step': 'name'} bot.send_message(message.chat.id, "📝 Mahsulot nomini kiriting:")

@bot.message_handler(content_types=['text']) def process_admin_steps(message): state = admin_states.get(message.chat.id) if not state: return if state['step'] == 'name': state['name'] = message.text state['step'] = 'price' bot.send_message(message.chat.id, "💵 Mahsulot narxini kiriting:") elif state['step'] == 'price': state['price'] = message.text state['step'] = 'category' markup = types.ReplyKeyboardMarkup(resize_keyboard=True) for cat in CATEGORIES: markup.add(cat) bot.send_message(message.chat.id, "🏷 Kategoriyani tanlang:", reply_markup=markup) elif state['step'] == 'category': if message.text not in CATEGORIES: bot.send_message(message.chat.id, "❌ Noto‘g‘ri kategoriya.") return state['category'] = message.text state['step'] = 'image' bot.send_message(message.chat.id, "📷 Mahsulot rasmini yuboring:", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(content_types=['photo']) def handle_product_photo(message): state = admin_states.get(message.chat.id) if not state or state.get('step') != 'image': return file_id = message.photo[-1].file_id product = { 'id': int(datetime.now().timestamp()), 'name': state['name'], 'price': state['price'], 'category': state['category'], 'image': file_id } save_product(product) del admin_states[message.chat.id] bot.send_message(message.chat.id, "✅ Mahsulot muvaffaqiyatli qo‘shildi!")

==== FLASK SERVER ====

@server.route(f"/{TOKEN}", methods=['POST']) def webhook(): update = telebot.types.Update.de_json(request.stream.read().decode("utf-8")) bot.process_new_updates([update]) return "", 200

@server.route('/') def home(): return 'Bot ishlayapti!'

if name == 'main': bot.remove_webhook() bot.set_webhook(url=WEBHOOK_URL) server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

