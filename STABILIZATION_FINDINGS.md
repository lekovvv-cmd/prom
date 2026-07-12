# PROM stabilization findings

## F-001 — старая модель platform roles

- Симптом: Projects JWT содержит только `sub`; platform role `admin` остаётся старым enum.
- Шаги воспроизведения: clean `docker compose up --build -d --wait`, вход `admin@utmn.ru`, проверка JWT/backend enum.
- Корневая причина: `create_access_token()` не записывает `platform_role`, `UserRole.ADMIN` не мигрирован в `platform_admin`.
- Исправление: в работе.
- Проверка: требуется role/JWT test и Docker role smoke.

## F-002 — employee ошибочно имеет Service Desk role

- Симптом: `employee@utmn.ru` после входа открывает `/service-desk`, видит каталог и Workbench как Service Desk manager.
- Шаги воспроизведения: production Nginx `http://localhost:5173/login?next=%2Fservice-desk` → выбрать сотрудника → войти.
- Корневая причина: Service Desk bootstrap/seed создаёт профиль для обычного Projects employee и выдаёт `service_desk.access`/`service_desk.be_assignee`.
- Исправление: в работе.
- Проверка: employee direct URL должен показать access denied, `/me` должен вернуть 403.

## F-003 — demo users не соответствуют stabilization prompt

- Симптом: login UI предлагает `admin@utmn.ru`, `manager@utmn.ru`, `employee@utmn.ru`; отсутствуют `project.manager@utmn.ru`, `sd.manager@utmn.ru`, `sd.admin@utmn.ru`.
- Шаги воспроизведения: открыть production `/login` после clean bootstrap.
- Корневая причина: Projects seed, Service Desk bootstrap и frontend demo-role list используют старый набор.
- Исправление: в работе.
- Проверка: вход всеми пятью целевыми ролями на clean и existing volumes.

## F-004 — закрытый каталог маркирован как публичный

- Симптом: после входа каталог показывает текст «Каталог доступен без входа».
- Шаги воспроизведения: войти в Service Desk и открыть `/service-desk`.
- Корневая причина: устаревший frontend copy и catalog API calls с `auth: false`.
- Исправление: в работе.
- Проверка: catalog endpoints без JWT возвращают 401; UI не содержит публичного обещания.

## F-005 — clean Docker baseline

- Симптом: первый запуск невозможен при остановленном Docker daemon; после запуска Docker Desktop clean build занимает около 9 минут из-за initial image/package download.
- Шаги воспроизведения: `docker compose down -v`, затем `docker compose up --build -d --wait`.
- Корневая причина: внешний prerequisite Docker Desktop был остановлен; кодовый bootstrap после запуска daemon завершился успешно.
- Исправление: код не требуется; wrapper должен ясно сообщать о недоступном daemon.
- Проверка: clean Compose завершился успешно; все DB/API/frontend/worker healthchecks green.

## F-006 — JWT не передавал platform role

- Симптом: Service Desk не мог отличить `platform_admin` по доверенному claim и всегда искал
  локальный `ServiceDeskUser`.
- Шаги воспроизведения: декодировать исходный Projects token — присутствовали только `sub` и
  `exp`; открыть Service Desk platform admin без локального profile — 403.
- Корневая причина: Projects не подписывал `platform_role`, Service Desk decoder возвращал
  только `sub`.
- Исправление: Projects подписывает `platform_role`; Service Desk валидирует подпись, срок,
  UUID subject и роль. `platform_admin` получает полный bypass.
- Проверка: API tests покрывают platform admin без заранее созданного profile, обе SD роли,
  employee/project manager без SD profile, inactive profile и поддельную подпись.
