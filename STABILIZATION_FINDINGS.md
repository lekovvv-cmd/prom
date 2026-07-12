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
- Исправление: catalog client использует bearer token; публичный copy удалён, backend routes
  закрыты `CurrentServiceDeskUser`.
- Проверка: catalog endpoints без JWT возвращают 401; frontend tests/build проходят, UI не
  содержит публичного обещания.

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

## F-007 — базовый доступ зависел от редактируемых capability

- Симптом: активный manager без `service_desk.access` получал 403, создание заявки отдельно
  требовало `service_desk.create_request`.
- Шаги воспроизведения: активировать manager с пустым capability set и вызвать `/me` или создать
  draft.
- Корневая причина: две базовые функции ошибочно находились в редактируемом capability enum.
- Исправление: обе capability удалены из enum/API/UI и legacy rows; активная роль включает вход,
  draft и submit.
- Проверка: API tests подтверждают `/me` и создание draft с пустым capability set.

## F-008 — устаревшие runtime-значения ролей

- Симптом: backend/frontend принимали `admin` и `manager`, но не целевые значения.
- Шаги воспроизведения: проверить enums и schema исходного HEAD.
- Корневая причина: отсутствовали сквозные migrations и синхронное обновление типов/guards.
- Исправление: migrations переименовывают роли в `platform_admin` и `service_desk_manager`;
  backend, frontend, seeds и tests обновлены синхронно.
- Проверка: clean migration chains, backend/frontend suites и TypeScript build проходят.

## F-009 — catalog API был публичным

- Симптом: четыре catalog/form endpoint отдавали данные без Service Desk principal.
- Шаги воспроизведения: вызвать `/categories`, `/services`, `/services/{id}` и form без token.
- Корневая причина: catalog router не зависел от `CurrentServiceDeskUser`.
- Исправление: все routes закрыты backend guard; frontend скрывает switch и показывает стабильный
  access denied без redirect-loop.
- Проверка: API regression проверяет 401 без token и доступ с активной ролью.

## F-010 — seed и bootstrap были двумя identity writers

- Симптом: catalog seed создавал старые profiles, bootstrap затем менял UUID и только добавлял
  capabilities; employee получал скрытый SD profile.
- Шаги воспроизведения: дважды запустить старые bootstrap/seed при изменённом Projects UUID.
- Корневая причина: два writer-а, неуникальный email и additive capability semantics.
- Исправление: Projects UUID — source; только platform-bootstrap синхронизирует/деактивирует
  profiles, catalog seed не пишет users. Capabilities заменяются, duplicate migration переносит
  FK references и создаёт unique email.
- Проверка: tests покрывают UUID repair, replace semantics, повторный запуск без дубля и отзыв
  доступа employee/project manager/platform admin.

## F-011 — submit validation завершалась без feedback

- Симптом: «Отправить заявку» визуально ничего не делала при пустых обязательных полях.
- Шаги воспроизведения: открыть форму услуги, очистить тему/описание и нажать submit.
- Корневая причина: страница не использовала HTML form; validation делала молчаливый `return`,
  а ошибки title/description не рендерились.
- Исправление: добавлены `<form onSubmit>`, submit button, общий и полевые errors,
  `aria-describedby`, focus/scroll первого invalid, pending state и синхронная double-submit lock.
  403/409/422/network errors преобразуются в понятные русские сообщения; draft остаётся отдельной
  кнопкой без submit-required validation.
- Проверка: frontend `82 passed`, TypeScript/Vite production build проходит. Production
  Playwright submit/draft/file/double-click ещё требует доступного Docker engine.

## F-012 — browser E2E обходил production stack

- Симптом: CI поднимал SQLite, два uvicorn и Vite вручную; PostgreSQL, Compose DAG, Nginx proxy,
  bootstrap jobs и SLA worker не участвовали.
- Шаги воспроизведения: проверить исходный job `e2e` в `.github/workflows/ci.yml`.
- Корневая причина: legacy dev-oriented orchestration внутри shell step.
- Исправление: job запускает `docker compose up --build -d --wait`, Playwright ходит через
  production Nginx, а failure artifacts включают Compose ps/logs, traces и screenshots.
- Проверка: Playwright discovery компилирует `12 tests` в трёх specs; фактический Docker run
  обновлённого job ожидает доступного engine/CI.
