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
    const targetUser = "{{ target_user }}"; // Передаем это значение из Flask

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
            if (data && data.message) {
                const sender = data.sender || "Неизвестно";
                addMessageToChat(sender, data.message, false, data.timestamp);
            }
        });

        // Обработка ошибок WebSocket
        socket.on("connect_error", (error) => {
            console.error("Ошибка подключения к WebSocket:", error);
        });

        socket.on("error", (error) => {
            console.error("Ошибка WebSocket:", error);
        });

        // Прокрутка вниз истории чата
        function scrollChatToBottom() {
            if (chatHistory) {
                chatHistory.scrollTo({
                    top: chatHistory.scrollHeight,
                    behavior: "smooth"
                });
            }
        }

        // Добавление сообщения в чат
        function addMessageToChat(sender, text, isUser, timestamp = null) {
            const message = document.createElement("div");
            message.className = isUser ? "message sent" : "message received";
            message.innerHTML = `
                <p><strong>${sender}:</strong> ${text}</p>
                <span class="timestamp">${timestamp ? new Date(timestamp).toLocaleString() : new Date().toLocaleString()}</span>
            `;
            chatHistory.appendChild(message);
            scrollChatToBottom();
        }

        // Сообщение о входе пользователя в чат
        socket.emit("join_chat", {
            chat_id: targetUser // Идентификатор чата
        });

        // Отправка сообщения о подключении пользователя
        socket.on("message", (data) => {
            if (data && data.msg) {
                addMessageToChat("Система", data.msg, false);
            }
        });
    }
});

// Функция открытия/закрытия бокового меню
function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const mainContent = document.getElementById("main-content");
    if (sidebar.style.width === "250px") {
        sidebar.style.width = "0";
        mainContent.classList.remove("menu-open");
    } else {
        sidebar.style.width = "250px";
        mainContent.classList.add("menu-open");
    }
}

// Улучшенная анимация для плавной прокрутки чата
const chatHistoryContainer = document.querySelector(".chat-history");
if (chatHistoryContainer) {
    chatHistoryContainer.addEventListener("scroll", () => {
        const scrollTop = chatHistoryContainer.scrollTop;
        const scrollHeight = chatHistoryContainer.scrollHeight;
        const clientHeight = chatHistoryContainer.clientHeight;

        if (scrollTop + clientHeight >= scrollHeight - 5) {
            chatHistoryContainer.style.scrollBehavior = "smooth";
        } else {
            chatHistoryContainer.style.scrollBehavior = "auto";
        }
    });
}
