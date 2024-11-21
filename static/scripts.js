document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript загружен и работает!");

    // Подключение WebSocket
    const socket = io.connect('http://' + document.domain + ':' + location.port);

    // Ссылки на элементы формы
    const sendMessageForm = document.getElementById('send-message-form');
    const messageInput = document.getElementById('message-input');
    const messagesContainer = document.getElementById('messages');
    const receiverIdInput = document.getElementById('receiver-id');

    // Обработчик отправки сообщения
    if (sendMessageForm) {
        sendMessageForm.addEventListener('submit', (event) => {
            event.preventDefault(); // Отключаем обновление страницы

            const receiverId = receiverIdInput ? receiverIdInput.value : null;
            const message = messageInput.value;

            if (!message.trim()) {
                alert('Введите сообщение!');
                return;
            }

            // Отправляем данные на сервер через WebSocket
            socket.emit('send_message', {
                receiver_id: receiverId,
                message: message
            });

            // Добавляем отправленное сообщение в контейнер
            addMessageToContainer('Вы', message);

            // Очищаем поле ввода
            messageInput.value = '';
        });
    }

    // Получение сообщения от сервера
    socket.on('receive_message', (data) => {
        addMessageToContainer(data.sender, data.message);
    });

    // Уведомление о закрытии чата
    socket.on('chat_closed', (data) => {
        alert(data.message);
    });

    // Анимация плавного появления содержимого
    const fadeContainers = document.querySelectorAll('.fade');
    fadeContainers.forEach(container => {
        container.style.opacity = 0;
        setTimeout(() => (container.style.opacity = 1), 50);
    });
});

// Функция добавления сообщения в контейнер
function addMessageToContainer(sender, message) {
    const newMessage = document.createElement('p');
    newMessage.textContent = `${sender}: ${message}`;
    newMessage.classList.add('message-item');
    const messagesContainer = document.getElementById('messages');
    if (messagesContainer) {
        messagesContainer.appendChild(newMessage);
        messagesContainer.scrollTop = messagesContainer.scrollHeight; // Прокручиваем вниз
    }
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
