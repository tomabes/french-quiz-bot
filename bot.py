import json
import random
import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from gtts import gTTS

# === Загрузка словаря ===
with open("french_vocab.json", encoding="utf-8") as f:
    vocab = json.load(f)

french_words = list(vocab.keys())
translations = list(vocab.values())
user_current_answer = {}
user_current_word = {}

# === Генерация вопроса ===
def generate_question():
    word = random.choice(french_words)
    correct = vocab[word]
    wrong_answers = random.sample([v for v in translations if v != correct], 3)
    options = wrong_answers + [correct]
    random.shuffle(options)
    return word, correct, options

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_question(update, context)

# === Обработка обычного ответа ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_answer = update.message.text
    correct_answer = user_current_answer.get(user_id)

    if correct_answer:
        if user_answer == correct_answer:
            await update.message.reply_text("✅ Верно!")
        else:
            await update.message.reply_text(f"❌ Неверно. Правильный ответ: {correct_answer}")

    await send_question(update, context)

# === Отправка нового вопроса ===
async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word, correct, options = generate_question()
    user_id = update.effective_user.id
    user_current_answer[user_id] = correct
    user_current_word[user_id] = word

    reply_markup = ReplyKeyboardMarkup([[opt] for opt in options], one_time_keyboard=True)
    audio_button = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🎧 Послушать", callback_data="pronounce")
    )

    await update.message.reply_text(f"💬 Что значит: *{word}* ?", parse_mode='Markdown', reply_markup=reply_markup)
    await update.message.reply_text("Нажми, чтобы услышать произношение:", reply_markup=audio_button)

# === Произношение слова ===
async def pronounce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    word = user_current_word.get(user_id, "Bonjour")

    tts = gTTS(word, lang='fr')
    filename = f"{user_id}_tts.mp3"
    tts.save(filename)

    with open(filename, 'rb') as audio:
        await update.callback_query.message.reply_voice(voice=InputFile(audio))
    await update.callback_query.answer()

    os.remove(filename)

# === Запуск через Webhook ===
async def main():
    TOKEN = "7666357029:AAFfc5DJ2p2zg4iLagvsRqu_3Wj980dkp2Y"
    URL = "https://french-quiz-bot.onrender.com/webhook"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(pronounce, pattern="^pronounce$"))

    await app.bot.set_webhook(URL)

    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path="webhook",
        webhook_url=URL
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
