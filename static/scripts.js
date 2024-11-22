document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript загружен и работает!");

    // Анимация плавного появления содержимого
    const fadeContainers = document.querySelectorAll('.fade');
    fadeContainers.forEach(container => {
        container.style.opacity = 0;
        setTimeout(() => (container.style.opacity = 1), 50);
    });

    // Подключение WebSocket и управление чатом
    const socket = io.connect();

    const chatHistory = document.querySelector(".chat-history");
    const chatForm = document.querySelector(".chat-form");
    const chatInput = document.querySelector(".chat-input");

    if (chatForm && chatHistory && chatInput) {
        // Подключение к комнате
        socket.emit('join', { receiver: "{{ target_user }}" });

        // Отправка сообщения
        chatForm.addEventListener("submit", (event) => {
            event.preventDefault();
            const messageText = chatInput.value.trim();
            if (messageText) {
                socket.emit('send_message', { 
                    receiver: "{{ target_user }}", 
                    message: messageText 
                });
                addMessageToChat("Вы", messageText, true);
                chatInput.value = "";
            }
        });

        // Получение нового сообщения
        socket.on('receive_message', (data) => {
            addMessageToChat(data.sender, data.message, false);
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
            message.style.alignSelf = "flex-start"; // Сообщения собеседника слева
        }

        chatHistory.appendChild(message);
        scrollChatToBottom();
    }

    // Боковая панель
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');

    // Функция открытия/закрытия боковой панели
    window.toggleSidebar = function () {
        if (sidebar.style.width === "250px") {
            sidebar.style.width = "0";
            mainContent.classList.remove('menu-open');
        } else {
            sidebar.style.width = "250px";
            mainContent.classList.add('menu-open');
        }
    };
});
