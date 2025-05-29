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

# Savatcha uchun vaqtinchalik xotira (oddiy misol uchun, realda bazaga yozish yaxshiroq)
user_carts = {}

# JSON saqlash/yuklash funksiyalari
def load_products():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

# Boshlang‘ich menyu (kategoriyalar + qidirish + savatcha)
def main_menu_markup(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in CATEGORIES:
        markup.add(types.KeyboardButton(cat))
    markup.add(types.KeyboardButton("🔍 Qidirish"))
    markup.add(types.KeyboardButton("🛒 Savatcha"))
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("➕ Mahsulot qo‘shish"))
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    markup = main_menu_markup(message.chat.id)
    bot.send_message(message.chat.id, "Assalomu alaykum! Kategoriya tanlang yoki qidirish tugmasini bosing:", reply_markup=markup)

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

# Kategoriya tanlanganida mahsulotlarni ko‘rsatish (savatchaga qo‘shish tugmasi bilan)
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
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛒 Savatchaga qo‘shish", callback_data=f"addcart_{p['name']}"))
        bot.send_photo(message.chat.id, p["photo"], caption=caption, reply_markup=markup)

# Callback query handler (savatchaga qo‘shish va buyurtma)
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    user_id = call.message.chat.id

    if data.startswith("addcart_"):
        product_name = data[len("addcart_"):]
        products = load_products()
        product = next((p for p in products if p["name"] == product_name), None)
        if not product:
            bot.answer_callback_query(call.id, "Mahsulot topilmadi.")
            return

        # Savatchaga qo‘shish
        cart = user_carts.get(user_id, [])
        cart.append(product)
        user_carts[user_id] = cart
        bot.answer_callback_query(call.id, f"✅ {product_name} savatchaga qo‘shildi.")

    elif data == "order_confirm":
        cart = user_carts.get(user_id, [])
        if not cart:
            bot.answer_callback_query(call.id, "Savatchingiz bo‘sh.")
            return

        order_text = f"📋 Yangi buyurtma:\n\n"
        for idx, p in enumerate(cart, 1):
            order_text += f"{idx}. {p['name']} — {p['price']}\n"

        order_text += f"\nBuyurtma beruvchi: @{call.message.chat.username} (ID: {user_id})"
        bot.send_message(ADMIN_ID, order_text)
        bot.answer_callback_query(call.id, "Buyurtma yuborildi. Rahmat!")
        user_carts[user_id] = []  # Savatchani tozalash

# "🔍 Qidirish" bosilganda mahsulot nomi uchun matn so‘rash
@bot.message_handler(func=lambda msg: msg.text == "🔍 Qidirish")
def search_start(message):
    bot.send_message(message.chat.id, "Qidiriladigan mahsulot nomini kiriting:")
    bot.register_next_step_handler(message, process_search)

def process_search(message):
    query = message.text.lower()
    products = load_products()
    found = [p for p in products if query in p["name"].lower()]

    if not found:
        bot.send_message(message.chat.id, "Hech qanday mahsulot topilmadi.")
        return

    for p in found:
        caption = f"📦 {p['name']}\n💰 {p['price']}\n📁 {p['category']}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛒 Savatchaga qo‘shish", callback_data=f"addcart_{p['name']}"))
        bot.send_photo(message.chat.id, p["photo"], caption=caption, reply_markup=markup)

# "🛒 Savatcha" ko‘rsatish
@bot.message_handler(func=lambda msg: msg.text == "🛒 Savatcha")
def show_cart(message):
    cart = user_carts.get(message.chat.id, [])
    if not cart:
        bot.send_message(message.chat.id, "Savatchingiz bo‘sh.")
        return

    text = "🛒 Savatchangizdagi mahsulotlar:\n\n"
    for idx, p in enumerate(cart, 1):
        text += f"{idx}. {p['name']} — {p['price']}\n"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Buyurtma berish", callback_data="order_confirm"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

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

# Webhook ni ishga tushirish
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
