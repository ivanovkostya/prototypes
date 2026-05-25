// Функция задержки
function delay(ms) {
    return new Promise((resolve) => {
        setTimeout(resolve, ms);
    });
}

// Имитация запроса
function fetchData(url) {
    return new Promise((resolve, reject) => {

        console.log(`Запрос по адресу: ${url}`);

        setTimeout(() => {

            if (url === "error") {
                reject("Ошибка запроса");
                return;
            }

            if (url === "users") {
                resolve([
                    { id: 1, name: "Алексей" },
                    { id: 2, name: "Мария" }
                ]);
            } else {
                resolve({ message: "Данные пользователя получены" });
            }

        }, 2000);
    });
}

// Асинхронная функция
async function loadData() {

    try {

        const users = await fetchData("users");

        console.log("Пользователи:");
        console.log(users);

        // Задержка между запросами
        await delay(1000);

        const firstUser = users[0];

        const userData = await fetchData(`user/${firstUser.id}`);

        console.log("Информация о пользователе:");
        console.log(userData);

    } catch (error) {

        console.log("Ошибка:");
        console.log(error);

    }
}

// Запуск функции
loadData();
