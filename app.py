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
    """Инициализация базы данных: создание файла и таблиц, если они отсутствуют."""
    if not os.path.exists(DATABASE):
        print("Создание базы данных...")
        try:
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
            cursor.close()
            conn.close()
            print("База данных успешно создана")
        except sqlite3.Error as e:
            print(f"Ошибка при создании базы данных: {e}")
    else:
        print("База данных уже существует")


def count_online_users():
    """Возвращает количество активных пользователей."""
    return len(session)


@app.route('/')
def home():
    """Главная страница: показывает количество пользователей и имя текущего пользователя."""
    username = session.get("username")

    # Проверяем наличие базы данных и таблицы
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

    # Получаем количество "активных" пользователей на сайте
    active_users = count_online_users()

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


@app.route('/rules')
def rules():
    """Страница с правилами использования."""
    return render_template('rules.html', title="Правила использования")


@app.route('/how_it_works')
def how_it_works():
    """Страница 'Как это работает'."""
    return render_template('how_it_works.html', title="Как это работает")


@app.route('/how_it_built')
def how_it_built():
    """Страница 'Как это устроено'."""
    return render_template('how_it_built.html', title="Как это устроено")


@app.route('/find_matches')
def find_matches():
    """Страница 'Найти совпадения'."""
    return render_template('find_matches.html', title="Найти совпадения")


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
            return redirect(url_for('home'))
        else:
            return "Неверное имя пользователя или пароль.", 400
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Выход из системы."""
    session.pop("username", None)
    return redirect(url_for('home'))


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
    init_db()  # Инициализация базы данных
    app.run(host='0.0.0.0', port=5000)
