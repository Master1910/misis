from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

# Создание приложения Flask
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Путь к файлу базы данных
DATABASE = os.path.join(os.getcwd(), "users.db")

# --- Утилитарные функции ---

def init_db():
    """Инициализация базы данных: создание файла и таблицы, если они отсутствуют."""
    if not os.path.exists(DATABASE):
        print("Создание базы данных...")
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
        print("База данных успешно создана")
    else:
        print("База данных уже существует")

def check_db():
    """Проверка существования таблицы 'users'."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    table_exists = cursor.fetchone()
    if table_exists:
        print("Таблица 'users' существует.")
    else:
        print("Таблица 'users' не существует!")
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
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            return "Пользователь с таким именем уже существует.", 400
    return render_template('register.html')

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/how_it_works')
def how_it_works():
    return render_template('how_it_works.html')

@app.route('/how_it_built')
def how_it_built():
    return render_template('how_it_built.html')

@app.route('/find_matches')
def find_matches():
    return render_template('find_matches.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE name = ?", (name,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session['username'] = name
            return redirect(url_for('home'))
        else:
            return "Неверное имя пользователя или пароль.", 400
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop("username", None)
    return redirect(url_for('home'))

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

# --- Запуск приложения ---
if __name__ == '__main__':
    init_db()  # Инициализация базы данных
    check_db()  # Проверка таблицы
    app.run(host='0.0.0.0', port=5000)
