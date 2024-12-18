const canvas = document.getElementById('tetris');
const context = canvas.getContext('2d');

// Размеры поля и блоков
const ROWS = 20;
const COLUMNS = 10;
const BLOCK_SIZE = 30;

canvas.width = COLUMNS * BLOCK_SIZE;
canvas.height = ROWS * BLOCK_SIZE;

context.scale(BLOCK_SIZE, BLOCK_SIZE);

// Игровое поле
let grid = Array.from({ length: ROWS }, () => Array(COLUMNS).fill(0));

// Формы фигур
const shapes = [
    [[1, 1, 1, 1]], // I
    [[1, 0, 0], [1, 1, 1]], // J
    [[0, 0, 1], [1, 1, 1]], // L
    [[1, 1], [1, 1]], // O
    [[0, 1, 1], [1, 1, 0]], // S
    [[0, 1, 0], [1, 1, 1]], // T
    [[1, 1, 0], [0, 1, 1]]  // Z
];

let currentPiece = randomPiece();
let position = { x: 3, y: 0 };

// Случайная фигура
function randomPiece() {
    const shape = shapes[Math.floor(Math.random() * shapes.length)];
    return shape;
}

// Рисование игрового поля и фигур
function draw() {
    context.fillStyle = '#222';
    context.fillRect(0, 0, canvas.width, canvas.height);

    drawGrid();
    drawPiece();
}

// Рисование сетки
function drawGrid() {
    context.strokeStyle = '#444';
    for (let y = 0; y < ROWS; y++) {
        for (let x = 0; x < COLUMNS; x++) {
            context.strokeRect(x, y, 1, 1);
            if (grid[y][x]) {
                context.fillStyle = 'cyan';
                context.fillRect(x, y, 1, 1);
            }
        }
    }
}

// Рисование текущей фигуры
function drawPiece() {
    context.fillStyle = 'cyan';
    currentPiece.forEach((row, y) => {
        row.forEach((value, x) => {
            if (value) {
                context.fillRect(position.x + x, position.y + y, 1, 1);
            }
        });
    });
}

// Проверка на столкновение
function collision() {
    return currentPiece.some((row, dy) =>
        row.some((value, dx) => value &&
            (grid[position.y + dy]?.[position.x + dx] !== 0 || position.x + dx < 0 || position.x + dx >= COLUMNS || position.y + dy >= ROWS)
        )
    );
}

// Опускание фигуры
function dropPiece() {
    position.y++;
    if (collision()) {
        position.y--;
        merge();
        resetPiece();
    }
    draw();
}

// Объединение фигуры с сеткой
function merge() {
    currentPiece.forEach((row, y) => {
        row.forEach((value, x) => {
            if (value) {
                grid[position.y + y][position.x + x] = value;
            }
        });
    });
    checkLines();
}

// Удаление заполненных линий
function checkLines() {
    grid = grid.filter(row => row.some(cell => cell === 0));
    while (grid.length < ROWS) {
        grid.unshift(Array(COLUMNS).fill(0));
    }
}

// Сброс новой фигуры
function resetPiece() {
    currentPiece = randomPiece();
    position = { x: 3, y: 0 };
    if (collision()) {
        grid = Array.from({ length: ROWS }, () => Array(COLUMNS).fill(0));
    }
}

// Движение фигуры
function movePiece(dir) {
    position.x += dir;
    if (collision()) position.x -= dir;
    draw();
}

// Вращение фигуры
function rotatePiece() {
    const prev = currentPiece;
    currentPiece = currentPiece[0].map((_, i) => currentPiece.map(row => row[i])).reverse();
    if (collision()) currentPiece = prev;
    draw();
}

// Обновление игры
setInterval(dropPiece, 500);
draw();
