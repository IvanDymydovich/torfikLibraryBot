import json
import os
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, CallbackQueryHandler, filters
)

ASK_TITLE, ASK_AUTHOR = range(2)
BOOKS_FILE = "books.json"

# Завантаження і збереження книг
def load_books():
    if os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_books(books):
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

my_books = load_books()

# Команда /start з кнопками
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📚 Список книжок", callback_data="books"),
            InlineKeyboardButton("➕ Додати книжку", callback_data="add")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Привіт! Обери дію нижче:",
        reply_markup=reply_markup
    )

# Обробка callback-кнопок
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "books":
        if not my_books:
            await query.edit_message_text("Список книжок порожній 😔")
        else:
            message = "Ось мої книжки:\n\n" + "\n".join(my_books)
            await query.edit_message_text(message)

    elif query.data == "add":
        await query.edit_message_text("Введи назву книжки 📖:")
        return ASK_TITLE

# Крок 1: Введення назви
async def ask_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Хто автор цієї книжки? ✍️")
    return ASK_AUTHOR

# Крок 2: Введення автора
async def finish_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    author = update.message.text
    title = context.user_data.get('title', 'Без назви')
    entry = f"📘 {title} — {author}"
    my_books.append(entry)
    save_books(my_books)
    await update.message.reply_text(f"✅ Книжку додано: {entry}")
    return ConversationHandler.END

# Вихід з діалогу
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Додавання скасовано.")
    return ConversationHandler.END

# Запуск
if __name__ == '__main__':
    TOKEN = "7838786752:AAEWC6yMnU9kqWa2mNMGMbYzwxK9rhsMOCU"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Кнопки меню
    app.add_handler(CallbackQueryHandler(handle_button, pattern="^books$"))
    # Діалог додавання
    conv_handler = ConversationHandler(
        per_message=True,
        entry_points=[
            CommandHandler("add", handle_button),
            CallbackQueryHandler(handle_button, pattern="^add$")
        ],
        states={
            ASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_author)],
            ASK_AUTHOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_add)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)

    print("✅ Бот працює з кнопками!")
    app.run_polling()
