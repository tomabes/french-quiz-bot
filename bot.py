import json
import random
import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from gtts import gTTS

# Global vocabularies and user state
available_vocab_files = {
    "🇫🇷 French": "french_vocab.json",
    "🌍 Nations": "vocab_nations.json",
    "🔢 Numbers 0–69": "vocab_numbers_69.json",
    "⚙️ Verbs": "vocab_verbs.json"
}

user_current_answer = {}
user_current_word = {}
user_vocab_choice = {}

# Load vocabulary
def load_vocab(filename):
    with open(filename, encoding="utf-8") as f:
        vocab = json.load(f)
    return vocab

# Generate a question
def generate_question(vocab):
    word = random.choice(list(vocab.keys()))
    correct = vocab[word]
    wrong_answers = random.sample([v for v in vocab.values() if v != correct], min(3, len(vocab)-1))
    options = wrong_answers + [correct]
    random.shuffle(options)
    return word, correct, options

# /start — select a vocabulary
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[vocab_name] for vocab_name in available_vocab_files]
    await update.message.reply_text(
        "👋 Choisis un dictionnaire pour commencer:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # If the user has not selected a vocabulary yet
    if user_id not in user_vocab_choice:
        if text not in available_vocab_files:
            await update.message.reply_text("❗️Ce dictionnaire n'est pas reconnu. Réessaie avec /start.")
            return

        vocab_file = available_vocab_files[text]
        vocab = load_vocab(vocab_file)
        user_vocab_choice[user_id] = vocab  # Store the vocabulary

        word, correct, options = generate_question(vocab)
        user_current_answer[user_id] = correct
        user_current_word[user_id] = word

        reply_markup = ReplyKeyboardMarkup([[opt] for opt in options], one_time_keyboard=True)
        audio_button = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("🎧 Écoute", callback_data="pronounce")
        )

        await update.message.reply_text(f"💬 Signifie: *{word}* ?", parse_mode='Markdown', reply_markup=reply_markup)
        await update.message.reply_text("Écoute la prononciation:", reply_markup=audio_button)

    else:
        # The user has already selected a vocabulary — check the answer
        vocab = user_vocab_choice[user_id]
        correct_answer = user_current_answer.get(user_id)

        if correct_answer:
            if text == correct_answer:
                await update.message.reply_text("✅ Bien!")
            else:
                await update.message.reply_text(f"❌ Faux. Réponse: {correct_answer}")

        # Next question
        word, correct, options = generate_question(vocab)
        user_current_answer[user_id] = correct
        user_current_word[user_id] = word

        reply_markup = ReplyKeyboardMarkup([[opt] for opt in options], one_time_keyboard=True)
        audio_button = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("🎧 Écoute", callback_data="pronounce")
        )

        await update.message.reply_text(f"💬 Signifie: *{word}* ?", parse_mode='Markdown', reply_markup=reply_markup)
        await update.message.reply_text("Écoute la prononciation:", reply_markup=audio_button)

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

# Start the bot
def main():
    application = ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(pronounce, pattern="^pronounce$"))
    application.run_polling()

if __name__ == "__main__":
    main()
