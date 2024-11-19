document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript загружен и работает!");

    // Подсветка активной ссылки в меню
    const navLinks = document.querySelectorAll("nav a");
    const currentPath = window.location.pathname;
    navLinks.forEach(link => {
        if (link.getAttribute("href") === currentPath) {
            link.classList.add("active");
        }
    });

    // Добавление всплывающего уведомления при клике на кнопку
    const buttons = document.querySelectorAll("button");
    buttons.forEach(button => {
        button.addEventListener("click", () => {
            showToast("Вы нажали кнопку!", "success");
        });
    });

    // Всплывающее уведомление
    function showToast(message, type) {
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        document.body.appendChild(toast);

        // Удаляем уведомление через 3 секунды
        setTimeout(() => {
            toast.classList.add("hide");
            setTimeout(() => toast.remove(), 500);
        }, 3000);
    }

    // Добавление эффекта появления на элементы при прокрутке
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("fade-in");
            }
        });
    });

    const fadeElements = document.querySelectorAll(".fade");
    fadeElements.forEach(el => observer.observe(el));
});
