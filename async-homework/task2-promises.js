// Функция имитирует запрос к серверу
function fetchData(url) {
    return new Promise((resolve, reject) => {

        console.log(`Запрос по адресу: ${url}`);

        setTimeout(() => {

            // Проверка на ошибку
            if (url === "error") {
                reject("Ошибка запроса");
                return;
            }

            // Имитация данных
            if (url === "users") {
                resolve([
                    { id: 1, name: "Алексей" },
                    { id: 2, name: "Мария" }
                ]);
            } else {
                resolve({ message: "Данные получены" });
            }

        }, 2000);
    });
}

// Цепочка Promise
fetchData("users")
    .then((users) => {

        console.log("Список пользователей:");
        console.log(users);

        // Берем первого пользователя
        const firstUser = users[0];

        return fetchData(`user/${firstUser.id}`);
    })
    .then((data) => {

        console.log("Информация о первом пользователе:");
        console.log(data);

    })
    .catch((error) => {

        console.log("Произошла ошибка:");
        console.log(error);

    });
