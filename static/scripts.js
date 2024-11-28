document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript загружен и работает!");

    // Анимация плавного появления содержимого
    const fadeContainers = document.querySelectorAll('.fade');
    fadeContainers.forEach(container => {
        container.style.opacity = 0;
        setTimeout(() => (container.style.opacity = 1), 50);
    });

    // Инициализация элементов чата
    const chatHistory = document.querySelector(".chat-history");
    const chatForm = document.querySelector("#chat-form");
    const chatInput = document.querySelector("#message-input");

    if (!chatHistory || !chatForm || !chatInput) {
        console.error("Не все элементы чата найдены на странице. Проверьте HTML.");
        return;
    }

    // Получаем имя целевого пользователя и текущего пользователя из контекста страницы
    const targetUser = "{{ target_user }}"; // Передается из Flask
    const currentUserId = {{ current_user_id }}; // Передается из Flask
    console.log(`Текущий пользователь ID: ${currentUserId}, Целевой пользователь: ${targetUser}`);

    // Подключение к WebSocket
    const socket = io.connect();

    // Обработка подключения WebSocket
    socket.on("connect", () => {
        console.log("WebSocket подключен");
        // Сообщение о входе пользователя в чат
        socket.emit("join_chat", {
            chat_id: targetUser
        });
    });

    socket.on("disconnect", () => {
        console.warn("WebSocket отключен");
    });

    socket.on("connect_error", (error) => {
        console.error("Ошибка подключения к WebSocket:", error);
    });

    // Обработка отправки сообщения
    chatForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const messageText = chatInput.value.trim();

        if (messageText) {
            console.log("Отправка сообщения:", messageText);
            // Отправка сообщения через WebSocket
            socket.emit("send_message", {
                receiver: targetUser,
                message: messageText
            });

            // Локальное добавление отправленного сообщения
            addMessageToChat("Вы", messageText, true);
            chatInput.value = "";
        } else {
            console.warn("Пустое сообщение нельзя отправить.");
        }
    });

    // Обработка входящих сообщений
    socket.on("receive_message", (data) => {
        if (data && data.message) {
            console.log("Получено сообщение:", data);
            const sender = data.sender || "Неизвестно";
            const isFromCurrentUser = data.sender_id === currentUserId;
            addMessageToChat(sender, data.message, isFromCurrentUser);
        } else {
            console.warn("Получено некорректное сообщение:", data);
        }
    });

    // Добавление сообщения в чат
    function addMessageToChat(sender, text, isUser) {
        const message = document.createElement("div");
        message.className = isUser ? "message sent" : "message received";
        message.innerHTML = `
            <p><strong>${sender}:</strong> ${text}</p>
        `;
        chatHistory.appendChild(message);
        scrollChatToBottom();
    }

    // Прокрутка вниз истории чата
    function scrollChatToBottom() {
        if (chatHistory) {
            chatHistory.scrollTo({
                top: chatHistory.scrollHeight,
                behavior: "smooth"
            });
        }
    }

    // Обработка системных сообщений
    socket.on("message", (data) => {
        if (data && data.msg) {
            console.log("Системное сообщение:", data.msg);
            addMessageToChat("Система", data.msg, false);
        }
    });

    // Обработка ошибок WebSocket
    socket.on("error", (error) => {
        console.error("Ошибка WebSocket:", error);
    });
});

// Функция открытия/закрытия бокового меню
function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const mainContent = document.getElementById("main-content");
    if (!sidebar || !mainContent) {
        console.error("Не найден элемент бокового меню.");
        return;
    }
    if (sidebar.style.width === "250px") {
        sidebar.style.width = "0";
        mainContent.classList.remove("menu-open");
    } else {
        sidebar.style.width = "250px";
        mainContent.classList.add("menu-open");
    }
}
