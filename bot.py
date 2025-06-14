import json
import random
import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from gtts import gTTS

# Глобальные словари и пользовательские состояния
available_vocab_files = {
    "🇫🇷 French": "french_vocab.json",
    "🌍 Nations": "vocab_nations.json",
    "🔢 Numbers 0–69": "vocab_numbers_69.json",
    "⚙️ Verbs": "vocab_verbs.json"
}

user_current_answer = {}
user_current_word = {}
user_vocab_choice = {}

# Загрузка словаря
def load_vocab(filename):
    with open(filename, encoding="utf-8") as f:
        vocab = json.load(f)
    return vocab

# Генерация вопроса
def generate_question(vocab):
    word = random.choice(list(vocab.keys()))
    correct = vocab[word]
    wrong_answers = random.sample([v for v in vocab.values() if v != correct], min(3, len(vocab)-1))
    options = wrong_answers + [correct]
    random.shuffle(options)
    return word, correct, options

# /start — выбор словаря
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[vocab_name] for vocab_name in available_vocab_files]
    await update.message.reply_text(
        "👋 Choisis un dictionnaire pour commencer:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

# Обработка выбора словаря
async def handle_vocab_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    choice = update.message.text

    if choice not in available_vocab_files:
        await update.message.reply_text("❗️Ce dictionnaire n'est pas reconnu. Réessaie avec /start.")
        return

    vocab_file = available_vocab_files[choice]
    vocab = load_vocab(vocab_file)
    user_vocab_choice[user_id] = vocab  # Сохраняем словарь

    word, correct, options = generate_question(vocab)
    user_current_answer[user_id] = correct
    user_current_word[user_id] = word

    reply_markup = ReplyKeyboardMarkup([[opt] for opt in options], one_time_keyboard=True)
    audio_button = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🎧 Écoute", callback_data="pronounce")
    )

    await update.message.reply_text(f"💬 Signifie: *{word}* ?", parse_mode='Markdown', reply_markup=reply_markup)
    await update.message.reply_text("Écoute la prononciation:", reply_markup=audio_button)

# Ответ пользователя
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_answer = update.message.text
    vocab = user_vocab_choice.get(user_id)

    if not vocab:
        await update.message.reply_text("ℹ️ D'abord choisis un dictionnaire via /start.")
        return

    correct_answer = user_current_answer.get(user_id)
    if correct_answer:
        if user_answer == correct_answer:
            await update.message.reply_text("✅ Bien!")
        else:
            await update.message.reply_text(f"❌ Faux. Réponse: {correct_answer}")

    word, correct, options = generate_question(vocab)
    user_current_answer[user_id] = correct
    user_current_word[user_id] = word

    reply_markup = ReplyKeyboardMarkup([[opt] for opt in options], one_time_keyboard=True)
    audio_button = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🎧 Écoute", callback_data="pronounce")
    )

    await update.message.reply_text(f"💬 Signifie: *{word}* ?", parse_mode='Markdown', reply_markup=reply_markup)
    await update.message.reply_text("Écoute la prononciation:", reply_markup=audio_button)

# Произношение
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

# Запуск
def main():
    application = ApplicationBuilder().token("7666357029:AAFfc5DJ2p2zg4iLagvsRqu_3Wj980dkp2Y").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vocab_selection))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(pronounce, pattern="^pronounce$"))
    application.run_polling()

if __name__ == "__main__":
    main()
