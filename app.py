from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import redis

# Создание приложения Flask
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# --- Конфигурация Redis для хранения сессий ---
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'session:'
# Использование предоставленного Redis URL
redis_url = 'redis://red-csud6tilqhvc73clb1q0:6379'
app.config['SESSION_REDIS'] = redis.StrictRedis.from_url(redis_url)

# Инициализация сессии
Session(app)

# Инициализация SocketIO
socketio = SocketIO(app, manage_session=False)

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
            cursor.execute('''CREATE TABLE IF NOT EXISTS interests (
                               user_id INTEGER,
                               interest TEXT,
                               FOREIGN KEY (user_id) REFERENCES users (id)
                            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               sender_id INTEGER,
                               receiver_id INTEGER,
                               message TEXT,
                               timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                               FOREIGN KEY (sender_id) REFERENCES users (id),
                               FOREIGN KEY (receiver_id) REFERENCES users (id)
                            )''')
            conn.commit()
            cursor.close()
            conn.close()
            print("База данных успешно создана")
        except sqlite3.Error as e:
            print(f"Ошибка при создании базы данных: {e}")
    else:
        print("База данных уже существует")

def find_users_with_common_interests(current_user_id):
    """Поиск пользователей с общими интересами."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT u.name
        FROM interests i1
        JOIN interests i2 ON i1.interest = i2.interest
        JOIN users u ON i2.user_id = u.id
        WHERE i1.user_id = ? AND i2.user_id != ?
    """, (current_user_id, current_user_id))
    matches = cursor.fetchall()
    conn.close()
    return [match[0] for match in matches]

# --- Маршруты ---
@app.route('/')
def home():
    """Главная страница."""
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

    try:
        active_users = len(app.config['SESSION_REDIS'].keys())  # Количество активных пользователей
    except redis.ConnectionError as e:
        print(f"Ошибка подключения к Redis: {e}")
        active_users = 0

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
            user_id = cursor.lastrowid
            interests_list = interests.split(',')
            for interest in interests_list:
                cursor.execute("INSERT INTO interests (user_id, interest) VALUES (?, ?)", (user_id, interest.strip()))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            return "Пользователь с таким именем уже существует.", 400
        except sqlite3.Error as e:
            return f"Ошибка базы данных: {e}", 500
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Авторизация пользователя."""
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

@app.route('/find_matches')
def find_matches():
    """Найти пользователей с общими интересами."""
    username = session.get("username")
    if not username:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE name = ?", (username,))
    user_id = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    matches = find_users_with_common_interests(user_id)
    return render_template('find_matches.html', matches=matches)

@app.route('/logout')
def logout():
    """Выход из системы."""
    session.pop("username", None)
    return redirect(url_for('home'))

# --- WebSocket ---
@socketio.on('send_message')
def handle_message(data):
    """Отправка сообщения."""
    sender = session.get("username")
    receiver = data['receiver']
    message = data['message']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO messages (sender_id, receiver_id, message)
        VALUES (
            (SELECT id FROM users WHERE name = ?),
            (SELECT id FROM users WHERE name = ?),
            ?
        )
    """, (sender, receiver, message))
    conn.commit()
    cursor.close()
    conn.close()

    emit('receive_message', {'sender': sender, 'message': message}, room=receiver)

@socketio.on('join')
def on_join(data):
    """Подключение к комнате."""
    username = session.get("username")
    join_room(username)

# --- Запуск ---
if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=5000)
