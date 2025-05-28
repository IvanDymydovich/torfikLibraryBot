import sqlite3

# Створюємо або відкриваємо базу
conn = sqlite3.connect("books.db")
cursor = conn.cursor()

# Створюємо таблицю
cursor.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT,
    filename TEXT
)
""")

# Приклад — додаємо одну книжку
cursor.execute("""
INSERT INTO books (title, author, filename)
VALUES (?, ?, ?)
""", ("Людина в пошуках сенсу", "Віктор Франкл", "людина_в_пошуках_сенсу.pdf"))

# Зберігаємо зміни та закриваємо з’єднання
conn.commit()
conn.close()

print("✅ База даних створена і книжка додана.")