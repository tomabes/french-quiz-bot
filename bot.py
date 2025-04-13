import json
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

with open("french_vocab.json", encoding="utf-8") as f:
    vocab = json.load(f)

french_words = list(vocab.keys())
translations = list(vocab.values())
user_current_answer = {}

def generate_question():
    word = random.choice(french_words)
    correct = vocab[word]
    wrong_answers = random.sample([v for v in translations if v != correct], 3)
    options = wrong_answers + [correct]
    random.shuffle(options)
    return word, correct, options

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word, correct, options = generate_question()
    user_current_answer[update.effective_user.id] = correct
    reply_markup = ReplyKeyboardMarkup([[opt] for opt in options], one_time_keyboard=True)
    await update.message.reply_text(f"💬 Что значит: *{word}* ?", parse_mode='Markdown', reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_answer = update.message.text
    correct_answer = user_current_answer.get(user_id)

    if correct_answer:
        if user_answer == correct_answer:
            await update.message.reply_text("✅ Верно!")
        else:
            await update.message.reply_text(f"❌ Неверно. Правильный ответ: {correct_answer}")

    word, correct, options = generate_question()
    user_current_answer[user_id] = correct
    reply_markup = ReplyKeyboardMarkup([[opt] for opt in options], one_time_keyboard=True)
    await update.message.reply_text(f"💬 Что значит: *{word}* ?", parse_mode='Markdown', reply_markup=reply_markup)

def main():
    application = ApplicationBuilder().token("7666357029:AAFfc5DJ2p2zg4iLagvsRqu_3Wj980dkp2Y").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()