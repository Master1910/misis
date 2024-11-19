document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript загружен и работает!");

    // Обрабатываем анимацию плавного появления содержимого
    const fadeContainers = document.querySelectorAll('.fade');
    fadeContainers.forEach(container => {
        container.style.opacity = 0;
        setTimeout(() => (container.style.opacity = 1), 50);
    });
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
