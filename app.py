from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

# Создание приложения Flask
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Путь к файлу базы данных
DATABASE = "users.db"

# --- Утилитарные функции ---
def init_db():
    """Инициализация базы данных: создание файла и таблицы, если они отсутствуют."""
    if os.path.exists(DATABASE) and not os.path.isfile(DATABASE):
        os.remove(DATABASE)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        institute TEXT,
                        interests TEXT
                     )''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    username = session.get("username")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()
    return render_template("home.html", user_count=user_count, username=username)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        password = generate_password_hash(request.form['password'])
        institute = request.form['institute']
        interests = request.form['interests']

        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, password, institute, interests) VALUES (?, ?, ?, ?)",
                           (name, password, institute, interests))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Пользователь с таким именем уже существует.", 400
    return render_template('register.html')

# --- Запуск приложения ---
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
