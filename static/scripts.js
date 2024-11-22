document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript загружен и работает!");

    // Подключение к WebSocket
    const socket = io.connect();

    // Элементы DOM
    const chatHistory = document.querySelector(".chat-history");
    const chatForm = document.querySelector(".chat-form");
    const chatInput = document.querySelector(".chat-input");

    // Подключаемся к комнате
    const targetUser = "{{ target_user }}"; // Django-шаблон для имени пользователя
    if (targetUser) {
        socket.emit('join', { receiver: targetUser });
    }

    // Анимация плавного появления содержимого
    const fadeContainers = document.querySelectorAll('.fade');
    fadeContainers.forEach(container => {
        container.style.opacity = 0;
        setTimeout(() => (container.style.opacity = 1), 50);
    });

    // Инициализация истории чата
    if (chatForm && chatHistory && chatInput) {
        chatForm.addEventListener("submit", (event) => {
            event.preventDefault();
            const messageText = chatInput.value.trim();
            if (messageText) {
                // Отправляем сообщение через WebSocket
                socket.emit('send_message', {
                    receiver: targetUser,
                    message: messageText
                });

                // Добавляем сообщение в интерфейс как отправленное пользователем
                addMessageToChat("Вы", messageText, true);
                chatInput.value = "";
            }
        });

        // Получение новых сообщений через WebSocket
        socket.on('receive_message', function(data) {
            const newMessage = document.createElement('div');
            newMessage.classList.add('message');
            newMessage.innerHTML = `
                <p><strong>${data.sender}:</strong> ${data.message}</p>
                <span class="timestamp">${new Date().toLocaleString()}</span>
            `;
            chatHistory.appendChild(newMessage);
            chatHistory.scrollTop = chatHistory.scrollHeight; // Автопрокрутка вниз
        });
    }

    // Прокрутка вниз истории чата
    function scrollChatToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // Добавление сообщения в чат
    function addMessageToChat(sender, text, isUser) {
        const message = document.createElement("div");
        message.className = "message";
        message.innerHTML = `
            <strong>${sender}:</strong> ${text}
            <span class="timestamp">${new Date().toLocaleTimeString()}</span>
        `;

        if (isUser) {
            message.style.alignSelf = "flex-end"; // Сообщения пользователя справа
        } else {
            message.style.alignSelf = "flex-start"; // Сообщения другого пользователя слева
        }

        chatHistory.appendChild(message);
        scrollChatToBottom();
    }

    // Функция открытия/закрытия бокового меню
    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('main-content');
        if (sidebar.style.width === "250px") {
            sidebar.style.width = "0";
            mainContent.classList.remove('menu-open');
        } else {
            sidebar.style.width = "250px";
            mainContent.classList.add('menu-open');
        }
    }
});
