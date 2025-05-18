import json
import random
import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from gtts import gTTS

# Загружаем словарь
with open("french_vocab.json", encoding="utf-8") as f:
    vocab = json.load(f)

french_words = list(vocab.keys())
translations = list(vocab.values())
user_current_answer = {}  # Храним правильные ответы по ID
user_current_word = {}    # Храним последнее слово по ID

# Генерация вопроса
def generate_question():
    word = random.choice(french_words)
    correct = vocab[word]
    wrong_answers = random.sample([v for v in translations if v != correct], 3)
    options = wrong_answers + [correct]
    random.shuffle(options)
    return word, correct, options

# Обработка /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word, correct, options = generate_question()
    user_id = update.effective_user.id
    user_current_answer[user_id] = correct
    user_current_word[user_id] = word

    reply_markup = ReplyKeyboardMarkup([[opt] for opt in options], one_time_keyboard=True)
    audio_button = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🎧 Écoute", callback_data="pronounce")
    )

    await update.message.reply_text(f"💬 Signifie: *{word}* ?", parse_mode='Markdown', reply_markup=reply_markup)
    await update.message.reply_text("Écoute la prononciation:", reply_markup=audio_button)

# Обработка текстовых ответов
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_answer = update.message.text
    correct_answer = user_current_answer.get(user_id)

    if correct_answer:
        if user_answer == correct_answer:
            await update.message.reply_text("✅ Bien!")
        else:
            await update.message.reply_text(f"❌ Faux. Réponse: {correct_answer}")

    word, correct, options = generate_question()
    user_current_answer[user_id] = correct
    user_current_word[user_id] = word

    reply_markup = ReplyKeyboardMarkup([[opt] for opt in options], one_time_keyboard=True)
    audio_button = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🎧 Écoute", callback_data="pronounce")
    )

    await update.message.reply_text(f"💬 Signifie: *{word}* ?", parse_mode='Markdown', reply_markup=reply_markup)
    await update.message.reply_text("Écoute la prononciation:", reply_markup=audio_button)

# Обработка кнопки "🎧 Послушать"
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

# Запуск бота
def main():
    application = ApplicationBuilder().token("7666357029:AAFfc5DJ2p2zg4iLagvsRqu_3Wj980dkp2Y").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(pronounce, pattern="^pronounce$"))
    application.run_polling()

if __name__ == "__main__":
    main()
