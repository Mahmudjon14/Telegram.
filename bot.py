
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

# Log sozlamalari
logging.basicConfig(level=logging.INFO)
TOKEN = "YOUR_BOT_TOKEN"

categories = {
    "🛠 Qurilish asboblari": ["Perforator", "Drel", "Bulgar"],
    "🏗 Og'ir texnikalar": ["Mini traktor", "Bobcat", "Ekskavator"],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[KeyboardButton(cat)] for cat in categories]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await update.message.reply_text("Kategoriya tanlang:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in categories:
        items = categories[text]
        await update.message.reply_text("\n".join(items))
    else:
        await update.message.reply_text("Iltimos, pastdagi tugmalardan birini tanlang.")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
