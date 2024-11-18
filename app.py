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

def count_online_users():
    """Подсчитывает количество активных пользователей на сайте (например, через сессии)."""
    # Для простоты можно использовать подсчет количества пользователей, которые вошли в систему.
    # В реальном приложении можно создать отдельную таблицу для логирования активности.
    return len(session)

@app.route('/')
def home():
    """Главная страница: показывает количество пользователей и имя текущего пользователя."""
    username = session.get("username")
    
    # Проверяем наличие базы данных и таблицы
    init_db()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()

    # Получаем количество "активных" пользователей на сайте
    active_users = count_online_users()

    return render_template("home.html", user_count=user_count, username=username, active_users=active_users)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя."""
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа пользователя."""
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
    """Выход из системы."""
    session.pop("username", None)
    return redirect(url_for('home'))

@app.errorhandler(500)
def internal_server_error(e):
    """Обработка ошибок сервера."""
    return render_template("500.html"), 500

# --- Запуск приложения ---
if __name__ == '__main__':
    init_db()  # Инициализация базы данных
    app.run(host='0.0.0.0', port=5000)
