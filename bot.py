import os
import sqlite3
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, filters
)

PDF_FOLDER = "pdf_books"
DB_PATH = "books.db"

# 📚 Функції для роботи з базою
def get_all_books():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author FROM books")
    books = cursor.fetchall()
    conn.close()
    return books

def get_random_books(n=3):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author FROM books ORDER BY RANDOM() LIMIT ?", (n,))
    books = cursor.fetchall()
    conn.close()
    return books

def get_book_file_by_id(book_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM books WHERE id = ?", (book_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# 🔘 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📚 Список книжок", callback_data="books"),
            InlineKeyboardButton("🎲 Що почитати?", callback_data="recommend")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привіт! Обери дію нижче:", reply_markup=reply_markup)

# 📥 /get назва
async def get_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❗ Напиши частину назви книжки після команди. Наприклад:\n"
            "`/get сенсу`", parse_mode="Markdown"
        )
        return

    keyword = " ".join(context.args).strip().lower()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM books WHERE LOWER(title) LIKE ?", (f"%{keyword}%",))
    result = cursor.fetchone()
    conn.close()

    if not result:
        await update.message.reply_text("📂 Цієї книжки не знайдено у форматі PDF 😔")
        return

    filename = result[0]
    file_path = os.path.join(PDF_FOLDER, filename)

    if os.path.exists(file_path):
        await update.message.chat.send_action(action=ChatAction.UPLOAD_DOCUMENT)
        await update.message.reply_document(document=open(file_path, "rb"), filename=filename)
    else:
        await update.message.reply_text("📂 Цієї книжки не знайдено у форматі PDF 😔")

# 🔘 Обробка кнопок
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "books":
        books = get_all_books()
        if not books:
            await query.edit_message_text("Список книжок порожній 😔")
        else:
            message = "Ось доступні книжки:\n\n"
            for book in books:
                message += f"📘 {book[1]} — {book[2]}\n"
            await query.edit_message_text(message)

    elif query.data == "recommend":
        books = get_random_books()
        if not books:
            await query.edit_message_text("📂 У мене ще немає книжок для порад 😥")
            return

        buttons = [
            [InlineKeyboardButton(f"📘 {title}", callback_data=f"get::{book_id}")]
            for book_id, title, author in books
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        text = "📖 *Що почитати сьогодні?*\n\n" + "\n".join(f"🔹 {b[1]} — {b[2]}" for b in books)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    elif query.data.startswith("get::"):
        book_id = query.data.replace("get::", "")
        filename = get_book_file_by_id(book_id)
        if not filename:
            await query.message.reply_text("📂 Цю книжку не знайдено у форматі PDF 😥")
            return

        file_path = os.path.join(PDF_FOLDER, filename)
        if os.path.exists(file_path):
            await query.message.chat.send_action(action=ChatAction.UPLOAD_DOCUMENT)
            await query.message.reply_document(document=open(file_path, "rb"), filename=filename)
        else:
            await query.message.reply_text("📂 Цю книжку не знайдено у форматі PDF 😥")

# 🚀 Запуск
if __name__ == '__main__':
    TOKEN = os.getenv("TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get", get_book))
    app.add_handler(CommandHandler("recommend", start))  # або зроби окрему recommend_books
    app.add_handler(CallbackQueryHandler(handle_button))

    print("✅ Бот працює!")
    app.run_polling()
