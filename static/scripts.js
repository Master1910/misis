document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript загружен и работает!");

    // Анимация плавного появления содержимого
    const fadeContainers = document.querySelectorAll('.fade');
    fadeContainers.forEach(container => {
        container.style.opacity = "0";
        setTimeout(() => {
            container.style.transition = "opacity 0.5s";
            container.style.opacity = "1";
        }, 50);
    });

    // Инициализация элементов чата
    const chatHistory = document.querySelector(".chat-history");
    const chatForm = document.querySelector("#chat-form");
    const chatInput = document.querySelector("#message-input");
    const chatId = chatHistory?.dataset.chatId || "";

    if (!chatHistory || !chatForm || !chatInput || !chatId) {
        console.warn("Элементы чата не найдены. Пропускаем функциональность чата.");
        return; // Прерываем выполнение, если элементы чата не найдены
    }

    console.log("Чат элементы найдены, продолжаем инициализацию.");

    const socket = io.connect();

    // Отправка сообщения
    chatForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const messageText = chatInput.value.trim();

        if (messageText) {
            socket.emit("send_message", { chat_id: chatId, message: messageText });
            addMessageToChat("Вы", messageText, true);
            chatInput.value = "";
        } else {
            console.warn("Пустое сообщение нельзя отправить.");
        }
    });

    // Обработка входящих сообщений
    socket.on("receive_message", (data) => {
        if (data && data.message && data.sender) {
            addMessageToChat(data.sender, data.message, false);
        }
    });

    // Обработка ошибок подключения WebSocket
    socket.on("connect_error", (error) => {
        console.error("Ошибка подключения к WebSocket:", error);
        addMessageToChat("Система", "Ошибка подключения к серверу.", false, true);
    });

    socket.on("error", (error) => {
        console.error("Ошибка WebSocket:", error);
        addMessageToChat("Система", "Ошибка WebSocket.", false, true);
    });

    // Добавление сообщения в чат
    function addMessageToChat(sender, text, isUser, isSystem = false) {
        const messageClass = isSystem ? "system-message" : isUser ? "message sent" : "message received";
        const message = `
            <div class="${messageClass}">
                <p><strong>${sender}:</strong> ${text}</p>
            </div>
        `;
        chatHistory.insertAdjacentHTML("beforeend", message);
        scrollChatToBottom();
    }

    // Прокрутка вниз истории чата
    function scrollChatToBottom() {
        chatHistory.scrollTo({
            top: chatHistory.scrollHeight,
            behavior: "smooth"
        });
    }

    // Уведомляем сервер о присоединении к чату
    socket.emit("join_chat", { chat_id: chatId });

    // Обработка системных сообщений
    socket.on("message", (data) => {
        if (data && data.msg) {
            addMessageToChat("Система", data.msg, false, true);
        }
    });

    // Обработка кнопок "Начать чат"
    const startChatButtons = document.querySelectorAll(".start-chat-btn");
    startChatButtons.forEach((button) => {
        button.addEventListener("click", (event) => {
            event.preventDefault();

            // Получение данных из атрибута кнопки
            const targetUserId = button.dataset.userId;

            if (!targetUserId) {
                console.error("Целевой пользователь не указан в data-user-id.");
                return;
            }

            // Отправка POST-запроса для создания нового чата
            fetch("/create_chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ target_user_id: targetUserId }),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success && data.chat_id) {
                        window.location.href = `/chat/${data.chat_id}`;
                    } else {
                        console.error("Не удалось создать чат:", data.error);
                    }
                })
                .catch((error) => console.error("Ошибка при создании чата:", error));
        });
    });

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
    } else {
        console.warn("Контейнер истории чата не найден.");
    }
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
