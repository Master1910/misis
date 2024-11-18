# Импорт библиотек
from flask import Flask, render_template, request, redirect, url_for, session
from pyngrok import ngrok
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Создание приложения Flask
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Путь к файлу базы данных
DATABASE = "users.db"

# Создание базы данных
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

# Главная страница
@app.route('/')
def home():
    username = session.get("username")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()
    return render_template("home.html", user_count=user_count, username=username)

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        institute = request.form.get('institute')
        interests = request.form.get('interests')

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, password, institute, interests) VALUES (?, ?, ?, ?)",
                (name, hashed_password, institute, interests)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Имя пользователя уже занято.", 400

    return render_template("register.html")

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE name = ?", (name,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = name
            return redirect(url_for('home'))
        else:
            return "Неверное имя пользователя или пароль.", 403

    return render_template("login.html")

# Страница правил
@app.route('/rules')
def rules():
    return render_template("rules.html")

# Как работает
@app.route('/how_it_works')
def how_it_works():
    return render_template("how_it_works.html")

# Как устроен
@app.route('/how_it_built')
def how_it_built():
    return render_template("how_it_built.html")

# Поиск пользователей с похожими интересами
@app.route('/find_matches')
def find_matches():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT interests FROM users WHERE id = ?", (session['user_id'],))
    user_interests = cursor.fetchone()[0]
    user_interests_set = set(user_interests.split(','))

    cursor.execute("SELECT name, interests FROM users WHERE id != ?", (session['user_id'],))
    potential_matches = []
    for name, interests in cursor.fetchall():
        interests_set = set(interests.split(','))
        shared_interests = user_interests_set & interests_set
        if shared_interests:
            potential_matches.append({"name": name, "shared_interests": list(shared_interests)})

    conn.close()
    return render_template("find_matches.html", matches=potential_matches)

# Выход из аккаунта
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Запуск приложения
if __name__ == '__main__':
    init_db()  # Инициализация базы данных

    # Установка authtoken для ngrok
    ngrok.set_auth_token("23ehCGThop4ZFUA6Dgem5CrxLUX_9ecaxq7T424nezcxMXni")

    # Подключение ngrok
    public_url = ngrok.connect(5000)
    print(f"Ваш сайт доступен по адресу: {public_url}")

    # Запуск Flask-сервера
    app.run(port=5000)
