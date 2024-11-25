from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extensions import parse_dsn
import os
import redis

# --- Конфигурация приложения ---
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# --- Конфигурация Redis для хранения сессий ---
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'session:'
redis_url = 'redis://red-csud6tilqhvc73clb1q0:6379'  # Замените на ваш URL, если он другой
app.config['SESSION_REDIS'] = redis.StrictRedis.from_url(redis_url)

# Инициализация сессий
Session(app)

# Инициализация WebSocket
socketio = SocketIO(app, manage_session=False)

# --- Конфигурация PostgreSQL ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:iXcGbtHYwmvJjpAfzUipRjFzIMMDttlo@autorack.proxy.rlwy.net:54163/railway")

ef get_db_connection():
    """Получение соединения с PostgreSQL."""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None
# --- Утилитарные функции ---
def init_db():
    """Инициализация базы данных."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Создание таблиц, если они не существуют
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                institute TEXT,
                interests TEXT
            );
        ''')
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS interests (
                user_id INTEGER REFERENCES users(id),
                interest TEXT
            );
        ''')
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                sender_id INTEGER REFERENCES users(id),
                receiver_id INTEGER REFERENCES users(id),
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        conn.commit()
        cursor.close()
        conn.close()
        print("База данных успешно инициализирована.")
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")

@app.route('/init_db')
def init_database():
    """Инициализация базы данных через веб-маршрут."""
    init_db()
    return "База данных инициализирована!"

# --- Маршруты ---
@app.route('/')
def home():
    """Главная страница."""
    username = session.get("username")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при выполнении запроса: {e}")
        user_count = 0

    try:
        active_users = len(app.config['SESSION_REDIS'].keys())
    except redis.ConnectionError as e:
        print(f"Ошибка подключения к Redis: {e}")
        active_users = 0

    return render_template("home.html", user_count=user_count, username=username, active_users=active_users)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        institute = request.form.get('institute')
        interests = request.form.get('interests')

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Добавление пользователя
            cursor.execute("""
                INSERT INTO users (name, password, institute, interests) 
                VALUES (%s, %s, %s, %s);
            """, (username, hashed_password, institute, interests))

            conn.commit()
            cursor.close()
            conn.close()

            session['username'] = username
            return redirect(url_for('home'))
        except psycopg2.IntegrityError:
            error = "Имя пользователя уже существует. Попробуйте другое."
            return render_template('register.html', title="Регистрация", error=error)

    return render_template('register.html', title="Регистрация")

def find_users_with_common_interests(user_id):
    """Поиск пользователей с общими интересами."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Получение интересов текущего пользователя
    cursor.execute("SELECT interests FROM users WHERE id = %s;", (user_id,))
    user_interests = cursor.fetchone()
    if not user_interests:
        return []

    user_interests = set(user_interests['interests'].split(','))

    # Поиск других пользователей с совпадающими интересами
    cursor.execute("SELECT id, name, interests FROM users WHERE id != %s;", (user_id,))
    all_users = cursor.fetchall()

    matches = []
    for other_user in all_users:
        other_interests_set = set(other_user['interests'].split(','))
        common_interests = user_interests.intersection(other_interests_set)
        if common_interests:
            matches.append({
                'id': other_user['id'],
                'name': other_user['name'],
                'common_interests': ', '.join(common_interests)
            })

    cursor.close()
    conn.close()
    return matches

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа пользователя."""
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        if not name or not password:
            return "Имя и пароль обязательны.", 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE name = %s;", (name,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and check_password_hash(user[0], password):
                session['username'] = name
                return redirect(url_for('home'))
            else:
                return "Неверное имя пользователя или пароль.", 400
        except Exception as e:
            return f"Ошибка базы данных: {e}", 500
    return render_template('login.html')


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
    username = session.get("username")
    if not username:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Получаем ID текущего пользователя
        cursor.execute("SELECT id FROM users WHERE name = %s;", (username,))
        user_row = cursor.fetchone()
        if not user_row:
            return "Пользователь не найден в базе данных.", 404

        user_id = user_row[0]
        matches = find_users_with_common_interests(user_id)

        return render_template('find_matches.html', title="Найти совпадения", matches=matches)

    except Exception as e:
        print(f"Ошибка базы данных: {e}")
        return "Произошла ошибка при поиске совпадений.", 500
#для создания чата
@app.route('/chat/<int:user_id>', methods=['GET'])
def chat(user_id):
    """Страница чата с другим пользователем."""
    current_user = session.get("username")
    if not current_user:
        return redirect(url_for('login'))

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Проверяем, существует ли пользователь
        cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
        target_user = cursor.fetchone()
        if not target_user:
            return "Пользователь не найден.", 404

        # Получаем историю сообщений
        cursor.execute("""
            SELECT sender_id, message, timestamp 
            FROM messages 
            WHERE (sender_id = (SELECT id FROM users WHERE name = ?) AND receiver_id = ?)
               OR (sender_id = ? AND receiver_id = (SELECT id FROM users WHERE name = ?))
            ORDER BY timestamp
        """, (current_user, user_id, user_id, current_user))
        messages = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('chat.html', messages=messages, target_user=target_user[0])

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return "Ошибка при загрузке чата.", 500



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


# --- WebSocket ---
@socketio.on('send_message')
def handle_message(data):
    """Отправка сообщения в комнату."""
    sender = session.get("username")
    receiver = data['receiver']
    message = data['message']

    if not sender or not receiver or not message:
        return

    # Создаем уникальное имя комнаты
    room = f"chat_{min(sender, receiver)}_{max(sender, receiver)}"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Сохраняем сообщение
        cursor.execute("""
            INSERT INTO messages (sender_id, receiver_id, message)
            VALUES (
                (SELECT id FROM users WHERE name = %s),
                (SELECT id FROM users WHERE name = %s),
                %s
            );
        """, (sender, receiver, message))
        conn.commit()

        emit('receive_message', {'sender': sender, 'message': message}, room=room)
    finally:
        cursor.close()
        conn.close()


@socketio.on('join')
def on_join(data):
    """Подключение к уникальной комнате."""
    sender = session.get("username")
    receiver = data['receiver']
    
    if not sender or not receiver:
        return

    # Создаем уникальное имя комнаты для пары пользователей
    room = f"chat_{min(sender, receiver)}_{max(sender, receiver)}"
    join_room(room)
    emit('room_joined', {'room': room}, room=room)



# --- Запуск ---
if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=5000)
