import os
import json
import random
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, CallbackQueryHandler, filters
)

ASK_TITLE, ASK_AUTHOR = range(2)
BOOKS_FILE = "books.json"
PDF_FOLDER = "pdf_books"

def load_books():
    if os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_books(books):
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

my_books = load_books()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📚 Список книжок", callback_data="books"),
            InlineKeyboardButton("➕ Додати книжку", callback_data="add")
        ],
        [InlineKeyboardButton("🎲 Що почитати?", callback_data="recommend")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привіт! Обери дію нижче:", reply_markup=reply_markup)

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

    elif query.data == "recommend":
        if not my_books:
            await query.edit_message_text("📂 У мене ще немає книжок для порад 😥")
            return

        recommendations = random.sample(my_books, min(3, len(my_books)))
        buttons = [
            [InlineKeyboardButton(f"📄 {title}", callback_data=f"get::{title}")]
            for title in recommendations
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        text = "📖 *Що почитати сьогодні?*\n\n" + "\n".join(f"🔹 {t}" for t in recommendations)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    elif query.data.startswith("get::"):
        name = query.data.replace("get::", "")
        filename = name.replace("📘 ", "").strip() + ".pdf"
        file_path = os.path.join(PDF_FOLDER, filename)

        if os.path.exists(file_path):
            await query.message.chat.send_action(action=ChatAction.UPLOAD_DOCUMENT)
            await query.message.reply_document(document=open(file_path, "rb"), filename=filename)
        else:
            await query.message.reply_text("📂 Цю книжку не знайдено у форматі PDF 😥")

async def ask_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Хто автор цієї книжки? ✍️")
    return ASK_AUTHOR

async def finish_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    author = update.message.text
    title = context.user_data.get('title', 'Без назви')
    entry = f"📘 {title} — {author}"
    my_books.append(entry)
    save_books(my_books)
    await update.message.reply_text(f"✅ Книжку додано: {entry}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Додавання скасовано.")
    return ConversationHandler.END

async def get_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❗ Напиши назву книжки після команди. Наприклад:\n"
            "`/get Наодинці з собою — Марк Аврелій`", parse_mode="Markdown"
        )
        return

    filename = " ".join(context.args).strip() + ".pdf"
    file_path = os.path.join(PDF_FOLDER, filename)

    if not os.path.exists(file_path):
        await update.message.reply_text("📂 Цієї книжки не знайдено у форматі PDF 😔")
        return

    await update.message.chat.send_action(action=ChatAction.UPLOAD_DOCUMENT)
    await update.message.reply_document(document=open(file_path, "rb"), filename=filename)

async def recommend_books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not my_books:
        await update.message.reply_text("📂 У мене ще немає книжок для порад 😥")
        return

    recommendations = random.sample(my_books, min(3, len(my_books)))
    buttons = [
        [InlineKeyboardButton(f"📄 {title}", callback_data=f"get::{title}")]
        for title in recommendations
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    text = "📖 *Що почитати сьогодні?*\n\n" + "\n".join(f"🔹 {t}" for t in recommendations)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

if __name__ == '__main__':
    TOKEN = os.getenv("TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get", get_book))
    app.add_handler(CommandHandler("recommend", recommend_books))

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
    app.add_handler(CallbackQueryHandler(handle_button))

    print("✅ Бот працює!")
    app.run_polling()
