from flask import Flask, render_template, request, redirect, url_for, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime

# Создание приложения Flask
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Путь к файлу базы данных
DATABASE = os.path.join(os.getcwd(), "users.db")


# --- Утилитарные функции ---
def init_db():
    """Инициализация базы данных: создание файла и таблиц, если они отсутствуют."""
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
        cursor.execute('''CREATE TABLE IF NOT EXISTS active_users (
                           username TEXT UNIQUE NOT NULL,
                           last_active DATETIME NOT NULL
                        )''')
        conn.commit()
        cursor.close()
        conn.close()
        print("База данных успешно создана")
    else:
        print("База данных уже существует")


def update_active_users(username):
    """Обновляет информацию об активности пользователя."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO active_users (username, last_active) VALUES (?, ?)",
        (username, datetime.now())
    )
    conn.commit()
    cursor.close()
    conn.close()


def count_active_users():
    """Возвращает количество активных пользователей."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Удаляем устаревших пользователей (например, неактивных более 10 минут)
    cursor.execute("DELETE FROM active_users WHERE last_active < datetime('now', '-10 minutes')")
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM active_users")
    active_users = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return active_users


def get_common_interests(username):
    """Возвращает список пользователей с общими интересами."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT interests FROM users WHERE name = ?", (username,))
    user_interests = cursor.fetchone()
    if not user_interests or not user_interests[0]:
        return []

    user_interests_set = set(user_interests[0].split(','))
    cursor.execute("SELECT name, interests FROM users WHERE name != ?", (username,))
    matches = []
    for row in cursor.fetchall():
        other_user, other_interests = row
        if other_interests:
            other_interests_set = set(other_interests.split(','))
            if user_interests_set & other_interests_set:  # Проверяем пересечение
                matches.append(other_user)

    cursor.close()
    conn.close()
    return matches


@app.route('/')
def home():
    """Главная страница: показывает количество пользователей и имя текущего пользователя."""
    username = session.get("username")
    init_db()

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
    except sqlite3.Error as e:
        print(f"Ошибка при выполнении запроса: {e}")
        user_count = 0

    active_users = count_active_users()

    return render_template("home.html", user_count=user_count, username=username, active_users=active_users)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя."""
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        institute = request.form.get('institute')
        interests = request.form.get('interests')

        if not name or not password:
            return "Имя и пароль обязательны.", 400

        password_hash = generate_password_hash(password)

        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, password, institute, interests) VALUES (?, ?, ?, ?)",
                           (name, password_hash, institute, interests))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            return "Пользователь с таким именем уже существует.", 400
        except sqlite3.Error as e:
            return f"Ошибка базы данных: {e}", 500
    return render_template('register.html')


@app.route('/find_matches')
def find_matches():
    """Страница 'Найти совпадения'."""
    username = session.get("username")
    if not username:
        abort(403)  # Доступ запрещен

    matches = get_common_interests(username)
    return render_template('find_matches.html', title="Найти совпадения", matches=matches)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа пользователя."""
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        if not name or not password:
            return "Имя и пароль обязательны.", 400

        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE name = ?", (name,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
        except sqlite3.Error as e:
            return f"Ошибка базы данных: {e}", 500

        if user and check_password_hash(user[0], password):
            session['username'] = name
            update_active_users(name)
            return redirect(url_for('home'))
        else:
            return "Неверное имя пользователя или пароль.", 400
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Выход из системы."""
    username = session.pop("username", None)
    if username:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM active_users WHERE username = ?", (username,))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('home'))


@app.route('/rules')
def rules():
    """Страница с правилами."""
    return render_template('rules.html', title="Правила использования")


@app.errorhandler(403)
def forbidden(e):
    """Обработка ошибки 403."""
    return render_template("403.html"), 403


@app.errorhandler(500)
def internal_server_error(e):
    """Обработка ошибки сервера."""
    return render_template("500.html"), 500


# --- Запуск приложения ---
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
