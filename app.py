from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
from flask_socketio import SocketIO, join_room, emit
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
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
# Получение строки подключения Redis из переменной окружения или дефолтного значения
redis_url = os.getenv('REDIS_URL', 'redis://red-ct2dkebtq21c738p0oo0:6379')
app.config['SESSION_REDIS'] = redis.StrictRedis.from_url(redis_url)
# Инициализация сессий
Session(app)
# Инициализация WebSocket
socketio = SocketIO(app)
# --- Утилитарные функции ---
import MySQLdb

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="81.200.146.168",
            user="gen_user",
            passwd="MasterElitVac",  # Замените на реальный пароль
            db="default_db",
            port=3306
        )
        print("Соединение с базой данных успешно установлено.")
        return conn
    except MySQLdb.Error as e:
        print(f"Ошибка подключения к MySQL: {e}")
        return None

        
def init_db():
    """Инициализация базы данных."""
    try:
        conn = get_db_connection()
        if not conn:
            print("Не удалось подключиться к базе данных.")
            return
        
        cursor = conn.cursor()
        
        # Создание таблицы пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                institute VARCHAR(255),
                interests TEXT
            );
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("База данных успешно инициализирована.")
    except MySQLdb.Error as e:
        print(f"Ошибка при инициализации базы данных: {e}")




@app.route('/init_db')
def init_database():
    """Инициализация базы данных через веб-маршрут."""
    try:
        init_db()
        return "База данных инициализирована!"
    except Exception as e:
        return f"Ошибка при инициализации базы данных: {e}"

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
        conn = get_db_connection()
        if not conn:
            return "Ошибка подключения к базе данных. Попробуйте позже.", 500
        try:
            cursor = conn.cursor()
            # Добавление пользователя
            cursor.execute("""
                INSERT INTO users (username, password, institute, interests) 
                VALUES (%s, %s, %s, %s);
            """, (username, hashed_password, institute, interests))
            conn.commit()
            cursor.close()
            conn.close()
            session['username'] = username
            return redirect(url_for('home'))
        except mysql.connector.IntegrityError:
            error = "Имя пользователя уже существует. Попробуйте другое."
            return render_template('register.html', title="Регистрация", error=error)
        except Exception as e:
            print(f"Ошибка базы данных: {e}")
            return "Произошла ошибка при регистрации.", 500
    return render_template('register.html', title="Регистрация")

def find_users_with_common_interests(user_id):
    """Поиск пользователей с общими интересами."""
    try:
        conn = get_db_connection()
        if not conn:
            print("Не удалось подключиться к базе данных.")
            return []

        cursor = conn.cursor(dictionary=True)

        # Получение интересов текущего пользователя
        cursor.execute("SELECT interests FROM users WHERE id = %s;", (user_id,))
        user_interests_row = cursor.fetchone()
        if not user_interests_row or not user_interests_row['interests']:
            print(f"Интересы текущего пользователя (ID: {user_id}) не найдены.")
            return []

        user_interests = set(user_interests_row['interests'].split(','))
        print(f"Интересы текущего пользователя: {user_interests}")

        # Поиск других пользователей с совпадающими интересами
        cursor.execute("SELECT id, username, interests FROM users WHERE id != %s;", (user_id,))
        all_users = cursor.fetchall()
        matches = []

        for other_user in all_users:
            if not other_user['interests']:
                continue
            other_interests_set = set(other_user['interests'].split(','))
            common_interests = user_interests.intersection(other_interests_set)
            if common_interests:
                matches.append({
                    'id': other_user['id'],
                    'name': other_user['username'],  # Меняем ключ username на name
                    'common_interests': ', '.join(common_interests)
                })

        print(f"Найдено совпадений: {len(matches)}")
        cursor.close()
        conn.close()
        return matches

    except Exception as e:
        print(f"Ошибка базы данных: {e}")
        return []


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа пользователя."""
    if request.method == 'POST':
        # Правильные названия для полей из формы
        username = request.form.get('username')  # Изменено на 'username'
        password = request.form.get('password')
        # Проверяем, что данные заполнены
        if not username or not password:
            return "Имя пользователя и пароль обязательны.", 400
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Поиск пользователя в базе данных по username
            cursor.execute("SELECT password FROM users WHERE username = %s;", (username,))
            user = cursor.fetchone()  # Вернёт None, если пользователь не найден
            cursor.close()
            conn.close()
            # Проверяем, найден ли пользователь, и совпадает ли пароль
            if user and check_password_hash(user[0], password):
                session['username'] = username
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
        
        # Поиск ID текущего пользователя
        cursor.execute("SELECT id FROM users WHERE username = %s;", (username,))
        user_row = cursor.fetchone()
        if not user_row:
            print(f"Пользователь {username} не найден в базе данных.")
            return "Пользователь не найден в базе данных.", 404
        
        user_id = user_row[0]
        print(f"ID текущего пользователя: {user_id}")
        
        # Поиск пользователей с общими интересами
        matches = find_users_with_common_interests(user_id)
        print(f"Найдено совпадений: {len(matches)}")
        
        return render_template('find_matches.html', matches=matches, current_user_id=user_id)
    except Exception as e:
        print(f"Ошибка базы данных: {e}")
        return "Ошибка поиска совпадений.", 500



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

# Маршрут для игры Тетрис
@app.route('/tetris')
def tetris():
    return render_template('tetris.html')


#все что связано с чатами
@socketio.on('join')
def on_join(data):
    username = session.get('username')
    if username:
        room = data['room']
        join_room(room)
        emit('message', {'msg': f'{username} joined the chat'}, room=room)

@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    message = data['message']
    username = session.get('username')
    
    # Сохранить сообщение в базе данных
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO messages (chat_id, sender_id, message)
                      VALUES (%s, %s, %s)''', (room, username, message))
    conn.commit()
    cursor.close()
    conn.close()
    
    # Отправить сообщение всем участникам чата
    emit('message', {'msg': f'{username}: {message}'}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = session.get('username')
    if username:
        room = data['room']
        emit('message', {'msg': f'{username} left the chat'}, room=room)
        leave_room(room)



# --- Запуск ---
if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=5000)
