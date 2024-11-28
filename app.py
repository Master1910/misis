from flask import Flask, render_template, request, redirect, url_for, session
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
# --- Конфигурация MySQL ---
DATABASE_URL = "mysql://root:lXTWowVLCSEKTJmXtFCQLNcmBRDxmgym@junction.proxy.rlwy.net:42004/railway"
# --- Утилитарные функции ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="junction.proxy.rlwy.net",
            port=42004,
            user="root",
            password="lXTWowVLCSEKTJmXtFCQLNcmBRDxmgym",
            database="railway"
        )
        print("Соединение с базой данных успешно установлено.")
        return conn
    except mysql.connector.Error as e:
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
        
        # Создание таблицы сообщений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT NOT NULL,
                receiver_id INT NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
            );
        ''')
        
        # Создание таблицы чатов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatss (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_1_id INT NOT NULL,
                user_2_id INT NOT NULL,
                active BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_1_id) REFERENCES users(id),
                FOREIGN KEY (user_2_id) REFERENCES users(id)
            );
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("База данных успешно инициализирована.")
    except mysql.connector.Error as e:
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
            return []
        cursor = conn.cursor(dictionary=True)  # Используем словарь для удобства работы с результатами
        # Получение интересов текущего пользователя
        cursor.execute("SELECT interests FROM users WHERE id = %s;", (user_id,))
        user_interests_row = cursor.fetchone()
        if not user_interests_row or not user_interests_row['interests']:
            return []
        user_interests = set(user_interests_row['interests'].split(','))  # Разделяем интересы на элементы
        # Поиск других пользователей с совпадающими интересами
        cursor.execute("SELECT id, username, interests FROM users WHERE id != %s;", (user_id,))
        all_users = cursor.fetchall()
        matches = []
        for other_user in all_users:
            # Убедимся, что у других пользователей есть интересы
            if not other_user['interests']:
                continue
            other_interests_set = set(other_user['interests'].split(','))
            common_interests = user_interests.intersection(other_interests_set)
            if common_interests:
                matches.append({
                    'id': other_user['id'],
                    'username': other_user['username'],  # Используем username
                    'common_interests': ', '.join(common_interests)
                })
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
        cursor.execute("SELECT id FROM users WHERE username = %s;", (username,))
        user_row = cursor.fetchone()
        if not user_row:
            return "Пользователь не найден в базе данных.", 404
        user_id = user_row[0]
        matches = find_users_with_common_interests(user_id)
        return render_template('find_matches.html', matches=matches, current_user_id=current_user_id)
    except Exception as e:
        print(f"Ошибка базы данных: {e}")
        return "Ошибка поиска совпадений.", 500

@app.route('/start_chat', methods=['POST'])
def start_chat():
    data = request.json

    # Проверка входных данных
    user_1_id = data.get('user_1_id')
    user_2_id = data.get('user_2_id')
    if not user_1_id or not user_2_id:
        return jsonify({'error': 'Некорректные данные.'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Проверяем существование чата
        query = """
            SELECT id FROM chatss
            WHERE (user_1_id = %s AND user_2_id = %s) OR (user_1_id = %s AND user_2_id = %s)
        """
        cursor.execute(query, (user_1_id, user_2_id, user_2_id, user_1_id))
        existing_chat = cursor.fetchone()

        if existing_chat:
            chat_id = existing_chat['id']
        else:
            # Создание нового чата
            insert_query = """
                INSERT INTO chatss (user_1_id, user_2_id, active) VALUES (%s, %s, 0)
            """
            cursor.execute(insert_query, (user_1_id, user_2_id))
            conn.commit()
            chat_id = cursor.lastrowid

        return jsonify({'chat_id': chat_id}), 200
    except Exception as e:
        print(f"Ошибка в start_chat: {e}")
        return jsonify({'error': 'Ошибка сервера.'}), 500
    finally:
        cursor.close()
        conn.close()



@app.route('/create_chat/<int:target_user_id>', methods=['POST'])
def create_chat(target_user_id):
    """Создание чата между текущим пользователем и другим пользователем."""
    current_user = session.get("username")
    if not current_user:
        return redirect(url_for("login"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Получение ID текущего пользователя
        cursor.execute("SELECT id FROM users WHERE username = %s", (current_user,))
        current_user_row = cursor.fetchone()
        if not current_user_row:
            return "Пользователь не найден в базе данных.", 404
        current_user_id = current_user_row["id"]

        # Проверка существования целевого пользователя
        cursor.execute("SELECT username FROM users WHERE id = %s", (target_user_id,))
        target_user = cursor.fetchone()
        if not target_user:
            return "Целевой пользователь не найден.", 404

        target_user_username = target_user["username"]

        # Создание чата (сохранение в базе данных)
        cursor.execute("INSERT INTO chatss (user_1_id, user_2_id) VALUES (%s, %s)", (current_user_id, target_user_id))
        conn.commit()

        return redirect(url_for('chat', user_id=target_user_id))

    except Exception as e:
        print(f"Ошибка при создании чата: {e}")
        return f"Ошибка при создании чата: {e}", 500

# Маршрут страницы чата
@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
def chat(user_id):
    """Чат между текущим пользователем и другим пользователем."""
    current_user = session.get("username")
    if not current_user:
        return redirect(url_for("login"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Получение ID текущего пользователя
        cursor.execute("SELECT id FROM users WHERE username = %s", (current_user,))
        current_user_row = cursor.fetchone()
        
        if not current_user_row:
            return "Пользователь не найден.", 404

        current_user_id = current_user_row["id"]

        # Получение информации о собеседнике
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        target_user = cursor.fetchone()
        
        if not target_user:
            return "Собеседник не найден.", 404

        target_user_username = target_user["username"]

        # Проверяем, что между пользователями есть активный чат
        cursor.execute("SELECT * FROM chatss WHERE (user_1_id = %s AND user_2_id = %s) OR (user_1_id = %s AND user_2_id = %s)", (current_user_id, user_id, user_id, current_user_id))
        chat = cursor.fetchone()

        if not chat:
            return "Чат не найден, создайте его.", 404

        return render_template("chat.html", target_user=target_user_username)

    except Exception as e:
        print(f"Ошибка при обработке чата: {e}")
        return f"Ошибка: {e}", 500



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

# WebSocket: отправка сообщений
@socketio.on("send_message")
def handle_send_message(data):
    """Обработка отправки сообщений."""
    sender = session.get("username")
    receiver = data.get("receiver")  # Используем имя получателя, как и на клиентской стороне
    message = data.get("message")

    # Отладочные сообщения
    print(f"Получены данные для отправки сообщения: sender: {sender}, receiver: {receiver}, message: {message}")

    if not sender or not receiver or not message:
        print("Ошибка: Неверные данные для отправки сообщения.")
        return

    # Подключение к базе данных
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)

            # Получаем ID отправителя
            cursor.execute("SELECT id FROM users WHERE username = %s", (sender,))
            sender_row = cursor.fetchone()
            if sender_row:
                sender_id = sender_row["id"]
                print(f"ID отправителя: {sender_id}")
            else:
                print(f"Не найден отправитель с именем {sender}")
                return

            # Получаем ID получателя
            cursor.execute("SELECT id FROM users WHERE username = %s", (receiver,))
            receiver_row = cursor.fetchone()
            if not receiver_row:
                print(f"Не найден получатель с именем {receiver}")
                return
            receiver_id = receiver_row["id"]
            print(f"ID получателя: {receiver_id}")

            # Находим или создаем чат
            cursor.execute(""" 
                SELECT id FROM chats 
                WHERE (user_1_id = %s AND user_2_id = %s) OR (user_1_id = %s AND user_2_id = %s)
            """, (sender_id, receiver_id, receiver_id, sender_id))
            existing_chat = cursor.fetchone()

            if not existing_chat:
                # Если чата нет, создаем новый
                cursor.execute(""" 
                    INSERT INTO chats (user_1_id, user_2_id, active) 
                    VALUES (%s, %s, 0)
                """, (sender_id, receiver_id))
                conn.commit()
                chat_id = cursor.lastrowid
                print(f"Создан новый чат с ID {chat_id}")
            else:
                chat_id = existing_chat["id"]
                print(f"Чат найден с ID {chat_id}")

            # Записываем сообщение в таблицу messs
            cursor.execute(""" 
                INSERT INTO messs (sender_id, receiver_id, message) 
                VALUES (%s, %s, %s)
            """, (sender_id, receiver_id, message))
            conn.commit()
            print("Сообщение успешно добавлено в таблицу messs.")

            # Уведомление участников чата
            room = f"chat_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"
            emit("receive_message", {
                "sender": sender,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "message": message
            }, room=room)

        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
        finally:
            cursor.close()
            conn.close()





# WebSocket: добавление пользователя в комнату
@socketio.on('join_chat')
def join_chat(data):
    """Подключение пользователя к комнате чата."""
    username = session.get("username")
    target_user_id = data.get("user_id")

    if not username or not target_user_id:
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Получение ID текущего пользователя
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        current_user_id = cursor.fetchone()["id"]

        # Формирование имени комнаты
        room = f"chat_{min(current_user_id, target_user_id)}_{max(current_user_id, target_user_id)}"

        # Подключаем пользователя к комнате
        join_room(room)

        # Уведомление участников
        emit("message", {"msg": f"{username} присоединился к чату."}, room=room)
    except Exception as e:
        print(f"Ошибка добавления в комнату: {e}")
    finally:
        cursor.close()
        conn.close()



@app.route('/get_chat_history', methods=['POST'])
def get_chat_history():
    data = request.json
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT sender_id, message
            FROM messs
            WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
            ORDER BY sender_id, receiver_id;
            """
            cursor.execute(query, (sender_id, receiver_id, receiver_id, sender_id))
            messages = cursor.fetchall()
            conn.close()
            return jsonify(messages), 200
        except Exception as e:
            return jsonify({"error": f"Ошибка при получении истории чатов: {e}"}), 500

@socketio.on("leave_chat")
def leave_chat(data):
    """Отключение пользователя от комнаты чата."""
    room = data.get("room")
    username = session.get("username")
    if username and room:
        leave_room(room)
        emit("message", {"msg": f"{username} покинул чат."}, room=room)



# --- Запуск ---
if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=5000)
