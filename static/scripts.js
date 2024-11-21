document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript загружен и работает!");

    // Подключение WebSocket
    const socket = io.connect(window.location.origin); // Используем window.location для универсальности

    // Ссылки на элементы формы
    const sendMessageForm = document.getElementById('send-message-form');
    const messageInput = document.getElementById('message-input');
    const messagesContainer = document.getElementById('messages');
    const receiverIdInput = document.getElementById('receiver-id');
    const closeChatBtn = document.getElementById('closeChatBtn'); // Кнопка закрытия чата

    // Проверка на существование элементов
    if (!sendMessageForm || !messageInput || !messagesContainer || !receiverIdInput) {
        console.error("Не все необходимые элементы найдены на странице!");
        return;
    }

    const receiverId = receiverIdInput.value;

    // Обработчик отправки сообщения
    sendMessageForm.addEventListener('submit', (event) => {
        event.preventDefault(); // Отключаем обновление страницы

        const message = messageInput.value;

        if (!message.trim()) {
            alert('Введите сообщение!');
            return;
        }

        // Отправляем сообщение на сервер через WebSocket
        socket.emit('send_message', {
            receiver_id: receiverId,
            message: message
        });

        // Добавляем отправленное сообщение в контейнер
        addMessageToContainer('Вы', message);

        // Очищаем поле ввода
        messageInput.value = '';
    });

    // Получение сообщения от сервера
    socket.on('receive_message', (data) => {
        addMessageToContainer(data.sender, data.message);
    });

    // Уведомление о закрытии чата
    socket.on('chat_closed', (data) => {
        alert(data.message);
        // Деактивируем все элементы, связанные с чатом
        closeChat();
    });

    // Закрытие чата
    closeChatBtn.addEventListener('click', () => {
        // Отправляем сигнал серверу о закрытии чата
        socket.emit('close_chat', { receiver_id: receiverId });
        closeChat();  // Обновляем интерфейс
    });

    // Функция добавления сообщения в контейнер
    function addMessageToContainer(sender, message) {
        const newMessage = document.createElement('p');
        newMessage.textContent = `${sender}: ${message}`;
        newMessage.classList.add('message-item');
        messagesContainer.appendChild(newMessage);
        messagesContainer.scrollTop = messagesContainer.scrollHeight; // Прокручиваем вниз
    }

    // Функция для закрытия чата (обновление UI)
    function closeChat() {
        closeChatBtn.disabled = true;
        messageInput.disabled = true;
        sendMessageForm.querySelector('button').disabled = true; // Отключаем кнопку отправки сообщений
        alert("Чат закрыт. Вы больше не можете отправлять сообщения.");
    }

    // Функция открытия/закрытия бокового меню
    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('main-content');
        
        if (!sidebar || !mainContent) {
            console.error('Элементы для боковой панели не найдены!');
            return;
        }

        if (sidebar.style.width === "250px") {
            sidebar.style.width = "0";
            mainContent.classList.remove('menu-open');
        } else {
            sidebar.style.width = "250px";
            mainContent.classList.add('menu-open');
        }
    }

    // Подключаем обработчик для кнопки боковой панели
    const sidebarButton = document.getElementById('sidebar-toggle-btn'); // Кнопка для открытия боковой панели
    if (sidebarButton) {
        sidebarButton.addEventListener('click', toggleSidebar);
    }

    // Анимация плавного появления содержимого
    const fadeContainers = document.querySelectorAll('.fade');
    fadeContainers.forEach(container => {
        container.style.opacity = 0;
        setTimeout(() => (container.style.opacity = 1), 50);
    });
});
