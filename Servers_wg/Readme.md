### Сборка и запуск
Перед запуском установить ip севрера в файле `docker-compose.yml`
```shell
docker-compose up -d --build
```
### Методы доступа к API
Добавление клиента
```shell
curl -X POST http://127.0.0.1:5000/add_client -H "Content-Type: application/json" -d '{"name": "test_client"}'
```
Удаление клиента
```shell
curl -X POST http://127.0.0.1:5000/remove_client -H "Content-Type: application/json" -d '{"name": "test_client"}'
```
Получение списка всех клиентов
```shell
curl -X GET http://127.0.0.1:5000/clients
```