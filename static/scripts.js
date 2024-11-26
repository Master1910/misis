document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript загружен и работает!");

    // Обрабатываем анимацию плавного появления содержимого
    const fadeContainers = document.querySelectorAll('.fade');
    fadeContainers.forEach(container => {
        container.style.opacity = 0;
        setTimeout(() => (container.style.opacity = 1), 50);
    });

    // Инициализация элементов чата
    const chatHistory = document.querySelector(".chat-history");
    const chatForm = document.querySelector("#chat-form");
    const chatInput = document.querySelector("#message-input");

    // Получаем имя целевого пользователя из контекста страницы
    const targetUser = "{{ target_user }}";  // Передаем это значение из Flask

    // Подключение к WebSocket
    const socket = io.connect();

    if (chatForm && chatHistory && chatInput) {
        // Отправка сообщения
        chatForm.addEventListener("submit", (event) => {
            event.preventDefault();
            const messageText = chatInput.value.trim();
            if (messageText) {
                // Отправка сообщения через WebSocket
                socket.emit("send_message", {
                    receiver: targetUser, // Целевой пользователь
                    message: messageText
                });

                // Локальное добавление отправленного сообщения
                addMessageToChat("Вы", messageText, true);
                chatInput.value = "";
            }
        });

        // Обработка полученных сообщений
        socket.on("receive_message", (data) => {
            addMessageToChat(data.sender, data.message, false);
        });

        // Прокрутка вниз истории чата
        function scrollChatToBottom() {
            if (chatHistory) {
                chatHistory.scrollTop = chatHistory.scrollHeight;
            }
        }

        // Добавление сообщения в чат
        function addMessageToChat(sender, text, isUser) {
            const message = document.createElement("div");
            message.className = isUser ? "message sent" : "message received";
            message.innerHTML = `
                <p><strong>${sender}:</strong> ${text}</p>
                <span class="timestamp">${new Date().toLocaleString()}</span>
            `;
            chatHistory.appendChild(message);
            scrollChatToBottom();
        }

        // Сообщение о входе пользователя в чат
        socket.emit('join_chat', {
            chat_id: targetUser  // Идентификатор чата
        });

        // Отправка сообщения о подключении пользователя
        socket.on('message', (data) => {
            addMessageToChat(data.msg, "", false);  // Добавляем сообщение о подключении в чат
        });
    }
});

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
