// Синхронный код выполняется сразу

console.log("1. Начало программы");

// setTimeout попадает в очередь macrotask
setTimeout(() => {
    console.log("4. setTimeout выполнен");
}, 0);

// Promise.then попадает в очередь microtask
Promise.resolve()
    .then(() => {
        console.log("3. Promise выполнен");
    });

// Этот код выполнится раньше асинхронных задач
console.log("2. Конец программы");

/*
Порядок выполнения:

1. Начало программы
2. Конец программы
3. Promise выполнен
4. setTimeout выполнен

Почему так происходит:
- Сначала выполняется весь синхронный код.
- Затем Event Loop выполняет microtask (Promise).
- После этого выполняются macrotask (setTimeout).
*/
