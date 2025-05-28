import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "7812379714:AAHeBy8IFoFZ60B8KRNIriSuDRYf_VlRVPs"
bot = telebot.TeleBot(TOKEN)

categories = {
    "🛠 Qurilish asboblari": ["Perforator", "Drel", "Bulgar"],
    "🏗 Og'ir texnikalar": ["Mini traktor", "Bobcat", "Ekskavator"],
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for category in categories:
        markup.add(KeyboardButton(category))
    bot.send_message(message.chat.id, "Kategoriya tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    if text in categories:
        items = categories[text]
        bot.send_message(message.chat.id, "\n".join(items))
    else:
        bot.send_message(message.chat.id, "Iltimos, pastdagi tugmalardan birini tanlang.")

bot.polling()
