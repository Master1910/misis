// Основной JavaScript-файл для взаимодействий на сайте
document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript загружен и работает!");
    
    // Пример обработки клика
    const buttons = document.querySelectorAll("button");
    buttons.forEach(button => {
        button.addEventListener("click", () => {
            alert("Кнопка нажата!");
        });
    });
});
