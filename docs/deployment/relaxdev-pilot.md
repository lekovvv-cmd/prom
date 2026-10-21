# Пилот PROM на RelaxDev

Разверните четыре отдельных проекта из репозитория `lekovvv-cmd/prom`, ветки `pilot/prom`. Во всех четырёх проектах выберите **Docker mode**, корень сборки — корень репозитория. Не выбирайте Service Desk. PostgreSQL создаётся в RelaxDev; контейнер с PostgreSQL не нужен. Серверный терминал не требуется. Названия пунктов панели и правило порта 8080 сверены с [документацией RelaxDev](https://relaxdev.ru/docs).

| Проект | Dockerfile path | База данных |
| --- | --- | --- |
| `prom-utmn-access` | `apps/access-service/Dockerfile` | своя Access PostgreSQL |
| `prom-utmn-projects` | `apps/projects/backend/Dockerfile` | своя Projects PostgreSQL |
| `prom-utmn-worker` | `apps/projects/backend/Dockerfile` | **та же** Projects PostgreSQL |
| `prom-utmn-shell` | `apps/platform-shell/Dockerfile.relaxdev` | не нужна |

1. Зарегистрируйтесь в RelaxDev и подключите GitHub-аккаунт, имеющий доступ к репозиторию.
2. Создайте проект `prom-utmn-access` из ветки `pilot/prom`, выберите Docker mode и указанный выше Dockerfile. Root directory — корень репозитория, build target и start command оставьте пустыми.
3. Создайте для Access управляемую PostgreSQL и привяжите её к проекту. Проверьте, что RelaxDev добавил `DATABASE_URL`.
4. Вставьте переменные из [`access.env.example`](../../deploy/relaxdev/access.env.example). Замените `ACCESS_JWT_PRIVATE_KEY` на личный PEM одной строкой, где переводы строк записаны как `\n`. Ключ можно создать локально через `deploy/relaxdev/generate-jwt-key.sh` (нужен OpenSSL); результат вставьте в панель как секрет. Не публикуйте ключ в GitHub.
5. Запустите deploy Access. Дождитесь успешной миграции и создания 12 пилотных учётных записей. Запишите фактический HTTPS URL Access, например `https://prom-utmn-access.relaxdev.ru`. Проверьте `/.well-known/jwks.json`.
6. Создайте проект `prom-utmn-projects` из той же ветки с Dockerfile из таблицы. Создайте **отдельную** управляемую Projects PostgreSQL и привяжите к нему; должен появиться `DATABASE_URL`.
7. Вставьте переменные из [`projects.env.example`](../../deploy/relaxdev/projects.env.example). В `PROJECTS_ACCESS_JWKS_URL` используйте фактический Access URL и суффикс `/.well-known/jwks.json`. Запустите deploy. Запишите фактический HTTPS URL Projects.
8. Создайте `prom-utmn-worker` из той же ветки и **того же Projects Dockerfile**. Скопируйте строку подключения Projects PostgreSQL в `PROJECTS_DATABASE_URL` worker (или подключите ту же БД так, чтобы `DATABASE_URL` указывал на неё). Не создавайте новую worker DB. Проверьте в логах worker успешное подключение: доступ другого проекта к приватной БД зависит от сетевых настроек RelaxDev. Если адрес БД недоступен, настройте доступ между проектами в панели или обратитесь в поддержку RelaxDev; не заменяйте строку подключения новой базой.
9. Вставьте переменные из [`worker.env.example`](../../deploy/relaxdev/worker.env.example), заменив адрес Access и строку БД. `PROJECTS_PROCESS=worker` запускает `python -m scripts.worker`; миграции и seed worker не выполняет. Запустите deploy.
10. Создайте `prom-utmn-shell` с `apps/platform-shell/Dockerfile.relaxdev`. Вставьте переменные из [`shell.env.example`](../../deploy/relaxdev/shell.env.example), указав фактические HTTPS URL Access и Projects **без завершающего `/`**. Запустите deploy и откройте Shell URL.
11. Проверьте вход одной из 12 пилотных учётных записей, каталог проектов, отклик, загрузку и скачивание вложения с разрешённой учётной записи. Проверьте, что другая учётная запись без доступа не может скачать вложение. После повторного deploy Projects скачивание должно продолжить работать. Проверьте обновление JWT после истечения короткого access token. Service Desk в пилоте отсутствует.

Shell направляет `/api/access/v1/*` и `/api/projects/v1/*` на публичные HTTPS адреса backend, сохраняя same-origin запросы браузера. Сборка frontend фиксирует `VITE_PLATFORM_ENVIRONMENT=pilot`, `VITE_ACCESS_API_BASE_URL=/api/access/v1`, `VITE_API_BASE_URL=/api/projects/v1`; build args вручную не требуются. `PORT` назначает RelaxDev. Access и Projects берут `DATABASE_URL`, если собственный `ACCESS_DATABASE_URL` или `PROJECTS_DATABASE_URL` не задан. Форматы `postgres://` и `postgresql://` автоматически переводятся на psycopg3. Вложения Projects хранятся в PostgreSQL при `PROJECTS_STORAGE_BACKEND=database`; локальное хранилище остаётся для Compose/Oracle.

Перезапуск web безопасен: Alembic применяет только новые миграции, seed синхронизирует пилотные записи без удаления существующих данных. Ошибка миграции останавливает deploy. Существующий [Oracle/VM сценарий](oracle-pilot.md) остаётся отдельным способом развертывания.
