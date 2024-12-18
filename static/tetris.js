const canvas = document.getElementById('tetris');
const context = canvas.getContext('2d');

// Настройки игрового поля
const ROWS = 20;
const COLUMNS = 10;
const BLOCK_SIZE = 30;

canvas.width = COLUMNS * BLOCK_SIZE;
canvas.height = ROWS * BLOCK_SIZE;

context.scale(BLOCK_SIZE, BLOCK_SIZE);

// Создание сетки
function createGrid(width, height) {
    const grid = [];
    while (height--) {
        grid.push(new Array(width).fill(0));
    }
    return grid;
}

// Проверка заполненных линий
function checkLines() {
    for (let y = grid.length - 1; y >= 0; y--) {
        if (grid[y].every(cell => cell !== 0)) {
            grid.splice(y, 1);
            grid.unshift(new Array(COLUMNS).fill(0));
            score += 10;
            updateScore();
        }
    }
}

// Обновление очков
let score = 0;
function updateScore() {
    document.querySelector('.score').innerText = `Очки: ${score}`;
}

// Управление фигурой
let currentPiece = createPiece();
let position = { x: 4, y: 0 };

// Функция создания случайной фигуры
function createPiece() {
    const pieces = 'IJLOSTZ';
    const type = pieces[Math.floor(Math.random() * pieces.length)];
    return shapes[type];
}

// Отрисовка фигуры
function drawPiece(piece, offset) {
    piece.forEach((row, y) => {
        row.forEach((value, x) => {
            if (value !== 0) {
                context.fillStyle = 'red';
                context.fillRect(x + offset.x, y + offset.y, 1, 1);
            }
        });
    });
}

// Перемещение фигуры вниз
function dropPiece() {
    position.y++;
    if (collision()) {
        position.y--;
        merge();
        checkLines();
        resetPiece();
    }
    draw();
}

// Проверка столкновений
function collision() {
    for (let y = 0; y < currentPiece.length; y++) {
        for (let x = 0; x < currentPiece[y].length; x++) {
            if (
                currentPiece[y][x] !== 0 &&
                (grid[position.y + y] &&
                grid[position.y + y][position.x + x]) !== 0
            ) {
                return true;
            }
        }
    }
    return false;
}

// Объединение фигуры с сеткой
function merge() {
    currentPiece.forEach((row, y) => {
        row.forEach((value, x) => {
            if (value !== 0) {
                grid[position.y + y][position.x + x] = value;
            }
        });
    });
}

// Сброс фигуры
function resetPiece() {
    currentPiece = createPiece();
    position = { x: 4, y: 0 };
    if (collision()) {
        grid = createGrid(COLUMNS, ROWS);
        score = 0;
        updateScore();
    }
}

// Основная функция отрисовки
function draw() {
    context.clearRect(0, 0, canvas.width, canvas.height);
    drawPiece(currentPiece, position);
}

// Запуск игры
let grid = createGrid(COLUMNS, ROWS);
updateScore();
setInterval(dropPiece, 1000);

// Управление с клавиатуры
document.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft') movePiece(-1);
    if (event.key === 'ArrowRight') movePiece(1);
    if (event.key === 'ArrowDown') dropPiece();
    if (event.key === ' ') dropInstantly();
});

// Перемещение фигуры
function movePiece(direction) {
    position.x += direction;
    if (collision()) position.x -= direction;
    draw();
}

// Мгновенное падение
function dropInstantly() {
    while (!collision()) position.y++;
    position.y--;
    merge();
    checkLines();
    resetPiece();
    draw();
}

// Создание элементов управления для телефона
function createMobileControls() {
    const controls = document.createElement('div');
    controls.classList.add('mobile-controls');
    controls.innerHTML = `
        <button onclick="movePiece(-1)">←</button>
        <button onclick="rotatePiece()">⟳</button>
        <button onclick="movePiece(1)">→</button>
        <button onclick="dropPiece()">↓</button>
    `;
    document.body.appendChild(controls);
}

// Вращение фигуры
function rotatePiece() {
    const prevPiece = currentPiece.map(row => [...row]);
    currentPiece = currentPiece[0].map((_, i) =>
        currentPiece.map(row => row[i]).reverse()
    );
    if (collision()) currentPiece = prevPiece;
    draw();
}

// Запуск мобильных кнопок
createMobileControls();

