import telebot
from telebot import types
import json
import os
from flask import Flask, request
from datetime import datetime

TOKEN = "7812379714:AAHeBy8IFoFZ60B8KRNIriSuDRYf_VlRVPs"
ADMIN_ID = 7864621105
WEBHOOK_URL = "https://telegram-botim.onrender.com"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

CATEGORIES = [
    "Beton aralashtirgichlar", "Perforatorlar", "Yuk ko‘taruvchi aravachalar", "Payvandlash apparatlari",
    "Plitalar", "Elektro instrumentlar", "Lazer o‘lchagichlar", "Zanjirli arra", "Slesar asboblari", "Burg‘ulash uskunalari"
]

DATA_FILE = "data/products.json"

# JSON saqlash/yuklash funksiyalari
def load_products():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

# Boshlash
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in CATEGORIES:
        markup.add(types.KeyboardButton(cat))
    if message.chat.id == ADMIN_ID:
        markup.add("➕ Mahsulot qo‘shish")
    bot.send_message(message.chat.id, "Assalomu alaykum! Kategoriya tanlang:", reply_markup=markup)

# Mahsulot qo‘shish bosqichlari
admin_states = {}
admin_data = {}

@bot.message_handler(func=lambda msg: msg.text == "➕ Mahsulot qo‘shish" and msg.chat.id == ADMIN_ID)
def add_product_start(message):
    admin_states[message.chat.id] = "name"
    admin_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "1️⃣ Mahsulot nomini kiriting:")

@bot.message_handler(func=lambda msg: admin_states.get(msg.chat.id) == "name")
def add_product_name(message):
    admin_data[message.chat.id]["name"] = message.text
    admin_states[message.chat.id] = "price"
    bot.send_message(message.chat.id, "2️⃣ Narxini kiriting:")

@bot.message_handler(func=lambda msg: admin_states.get(msg.chat.id) == "price")
def add_product_price(message):
    admin_data[message.chat.id]["price"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for cat in CATEGORIES:
        markup.add(cat)
    admin_states[message.chat.id] = "category"
    bot.send_message(message.chat.id, "3️⃣ Kategoriyani tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda msg: admin_states.get(msg.chat.id) == "category")
def add_product_category(message):
    admin_data[message.chat.id]["category"] = message.text
    admin_states[message.chat.id] = "photo"
    bot.send_message(message.chat.id, "4️⃣ Mahsulot rasmini yuboring (jpg, png)...")

@bot.message_handler(content_types=["photo"])
def add_product_photo(message):
    if admin_states.get(message.chat.id) != "photo":
        return
    file_id = message.photo[-1].file_id
    admin_data[message.chat.id]["photo"] = file_id
    admin_data[message.chat.id]["timestamp"] = datetime.now().isoformat()

    products = load_products()
    products.append(admin_data[message.chat.id])
    save_products(products)

    bot.send_message(message.chat.id, "✅ Mahsulot muvaffaqiyatli qo‘shildi!")

    admin_states.pop(message.chat.id, None)
    admin_data.pop(message.chat.id, None)

# Kategoriya tanlanganida mahsulotlarni ko‘rsatish
@bot.message_handler(func=lambda msg: msg.text in CATEGORIES)
def show_products(message):
    category = message.text
    products = load_products()
    items = [p for p in products if p["category"] == category]

    if not items:
        bot.send_message(message.chat.id, "Bu toifadagi mahsulotlar hali mavjud emas.")
        return

    for p in items:
        caption = f"📦 {p['name']}\n💰 {p['price']}\n📁 {p['category']}"
        bot.send_photo(message.chat.id, p["photo"], caption=caption)

# Webhook bilan Flask server
@app.route('/', methods=["GET", "POST"])
def webhook():
    if request.method == "POST":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    else:
        return "Bot ishga tushdi!"

# Webhookni o'rnatish (bir marta ishlatiladi)
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# ⚠️ `app.run(...)` olib tashlandi, chunki endi gunicorn ishlatiladi
