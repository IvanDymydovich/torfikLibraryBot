import os
import json
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, CallbackQueryHandler, filters
)

# Стани діалогу
ASK_TITLE, ASK_AUTHOR = range(2)

# Файл і папка для збереження
BOOKS_FILE = "books.json"
PDF_FOLDER = "pdf_books"

# ----------------------------------------
# 🔃 Завантаження/збереження книжок
# ----------------------------------------

def load_books():
    if os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_books(books):
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

my_books = load_books()

# ----------------------------------------
# 📚 Обробники
# ----------------------------------------

# Команда /start
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

# Обробка кнопок
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

# Початок діалогу /add
async def ask_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Хто автор цієї книжки? ✍️")
    return ASK_AUTHOR

# Завершення діалогу
async def finish_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    author = update.message.text
    title = context.user_data.get('title', 'Без назви')
    entry = f"📘 {title} — {author}"
    my_books.append(entry)
    save_books(my_books)
    await update.message.reply_text(f"✅ Книжку додано: {entry}")
    return ConversationHandler.END

# Скасування додавання
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Додавання скасовано.")
    return ConversationHandler.END

# Отримати PDF книжку
async def get_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❗ Напиши назву книжки після команди. Наприклад:\n"
            "`/get Маленький принц — Екзюпері`", parse_mode="Markdown"
        )
        return

    filename = " ".join(context.args).strip() + ".pdf"
    file_path = os.path.join(PDF_FOLDER, filename)

    if not os.path.exists(file_path):
        await update.message.reply_text("📂 Цієї книжки не знайдено у форматі PDF 😔")
        return

    await update.message.chat.send_action(action=ChatAction.UPLOAD_DOCUMENT)
    await update.message.reply_document(document=open(file_path, "rb"), filename=filename)

# ----------------------------------------
# 🏁 Запуск бота
# ----------------------------------------

if __name__ == '__main__':
    TOKEN = os.getenv("TOKEN")  # 🔐 Безпечне завантаження токена

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get", get_book))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="^books$"))

    # Діалогове додавання
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

    print("✅ Бот працює!")
    app.run_polling()
