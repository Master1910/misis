document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript загружен и работает!");

    // Обрабатываем анимацию плавного появления содержимого
    const fadeContainers = document.querySelectorAll('.fade');
    fadeContainers.forEach(container => {
        container.style.opacity = 0;
        setTimeout(() => (container.style.opacity = 1), 50);
    });

    // Инициализация истории чата
    const chatHistory = document.querySelector(".chat-history");
    const chatForm = document.querySelector(".chat-form");
    const chatInput = document.querySelector(".chat-input");

    if (chatForm && chatHistory && chatInput) {
        chatForm.addEventListener("submit", (event) => {
            event.preventDefault();
            const messageText = chatInput.value.trim();
            if (messageText) {
                addMessageToChat("Вы", messageText, true);
                chatInput.value = "";

                // Имитируем ответ от бота
                setTimeout(() => {
                    addMessageToChat("Бот", "Ваше сообщение обработано!", false);
                }, 1000);
            }
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
            message.style.alignSelf = "flex-start"; // Сообщения бота слева
        }

        chatHistory.appendChild(message);
        scrollChatToBottom();
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
