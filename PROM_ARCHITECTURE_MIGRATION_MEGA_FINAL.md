# PROM: полный переход на масштабируемую продуктовую архитектуру

## Роль исполнителя

Ты — ведущий архитектор и senior full-stack engineer. Твоя задача — **самостоятельно перестроить текущий репозиторий `lekovvv-cmd/prom` из текущего состояния в production-ready платформенную архитектуру**, рассчитанную на последовательное добавление третьего, четвёртого, пятого и следующих крупных бизнес-модулей.

Не ограничивайся рекомендациями, схемами или частичными заготовками. Внеси реальные изменения в код, структуру репозитория, Docker Compose, CI, документацию и тесты.

Работай от текущего состояния ветки `main`.

Перед проектированием целевой структуры проведи критический аудит существующей реализации. Не считай текущий код эталоном: найди мёртвый код, дубли, неоптимальные решения, архитектурные нарушения и ненужные зависимости. Безопасно удали лишнее и улучши слабые места, подтверждая изменения тестами и измерениями.

---

# 1. Главная цель

Нужно получить монорепозиторий платформы PROM, в котором:

- каждый крупный бизнес-модуль является самостоятельным bounded context;
- каждый крупный модуль может иметь собственный backend, frontend-часть, базу данных, миграции, worker-ы и тесты;
- все модули используют единый платформенный frontend shell;
- аутентификация подготовлена к переходу на SSO ТюмГУ;
- внутри платформы остаётся централизованный RBAC;
- конкретные объектные бизнес-права остаются внутри самих модулей;
- общая инфраструктурная логика не копируется между backend;
- новый модуль можно добавить по стандартному шаблону без переделки всей платформы;
- локальная разработка, тестирование и production-like запуск остаются простыми;
- существующие PROM Projects и Service Desk продолжают работать без функционального отката.

Целевая модель:

```text
SSO ТюмГУ
    │
    ▼
Gateway / Platform access
    │
    ├── Platform shell
    │
    ├── Access / RBAC service
    │
    ├── Projects
    │
    ├── Service Desk
    │
    ├── Module 3
    │
    ├── Module 4
    │
    └── Module 5
```

---

# 2. Важные исходные условия

Учитывай следующие зафиксированные решения:

1. Каждый будущий модуль будет крупным и сложным.
2. Каждый крупный модуль должен иметь возможность независимого развития и отдельного релиза.
3. Аутентификация в будущем полностью перейдёт под SSO ТюмГУ.
4. Наша зона ответственности после SSO:
   - платформа;
   - внутренний профиль пользователя;
   - доступ к модулям;
   - RBAC;
   - локальные capabilities;
   - объектные domain policies;
   - аудит прав.
5. Сейчас реальных параметров SSO ТюмГУ может не быть.
6. Поэтому нужно:
   - создать production-ready authentication abstraction;
   - реализовать локальный SSO mock;
   - оставить OIDC/SAML-ready интеграционную точку;
   - не блокировать архитектурную миграцию отсутствием реальных SSO URL и client credentials.
7. Не вводить микросервисы ради микросервисов.
8. Один крупный продуктовый модуль — один крупный сервис, а не десятки мелких сервисов.
9. Не вводить microfrontend до тех пор, пока модули не начнут выпускаться независимыми командами.
10. Сейчас должен остаться один frontend build с lazy-loaded модулями и единым shell.
11. Service Desk остаётся самостоятельным backend и самостоятельной базой.
12. Projects становится самостоятельным продуктовым модулем, а не владельцем идентичности всей платформы.
13. Новый третий модуль должен добавляться по готовому шаблону.

---

# 3. Текущее состояние, которое нельзя сломать

В репозитории сейчас существуют:

```text
backend/
service-desk-backend/
frontend/
docker-compose.yml
.github/workflows/ci.yml
```

Функционально есть два продукта.

## Projects

- пользователи;
- текущая локальная авторизация;
- проекты;
- отклики;
- участники;
- задачи;
- отчёты;
- административные операции.

## Service Desk

- каталог;
- динамические формы;
- черновики;
- заявки;
- вложения;
- согласования;
- маршрутизация;
- SLA;
- рабочие календари;
- эскалации;
- уведомления;
- transactional outbox;
- рабочее место;
- RBAC/capabilities;
- worker SLA.

Текущий frontend обслуживает оба продукта.

Текущий Docker Compose поднимает:

- Projects PostgreSQL;
- Service Desk PostgreSQL;
- миграции;
- seed;
- identity bootstrap;
- два API;
- SLA worker;
- frontend/Nginx.

Текущий CI проверяет:

- pytest Projects;
- pytest Service Desk;
- Ruff Service Desk;
- PostgreSQL concurrency Service Desk;
- Vitest;
- frontend build;
- production-like Docker Compose E2E через Playwright.

Все существующие сценарии должны продолжить работать.

---

# 4. Главный принцип выполнения

Не делай полный rewrite.

Используй стратегию:

```text
переместить
→ стабилизировать
→ выделить общую платформу
→ заменить связи
→ разделить frontend
→ улучшить CI
→ подтвердить тестами
```

На каждом этапе приложение должно оставаться запускаемым.

Не удаляй рабочую бизнес-логику только ради красивой структуры.

Не заменяй проверенные механизмы Service Desk упрощёнными заглушками.

Особенно сохранить:

- state machine заявок;
- snapshots;
- SLA engine;
- PostgreSQL locking;
- outbox;
- approval workflow;
- routing;
- защищённые вложения;
- existing permissions;
- health/readiness;
- миграции;
- тесты.

---


# 4.1. Обязательный аудит, удаление мёртвого кода и улучшение реализации

Архитектурная миграция не должна быть механическим переносом старого кода в новые каталоги.

До структурных изменений проведи полный технический аудит всего репозитория, а затем продолжай аудит во время каждого этапа миграции.

Цель:

```text
не сохранить старую сложность в новых папках,
а получить более простой, быстрый, понятный и поддерживаемый код
```

## 4.1.1. Сначала зафиксируй baseline

До крупных изменений:

1. зафиксируй текущее дерево репозитория;
2. запусти все существующие тесты;
3. собери frontend production build;
4. запусти production-like Docker Compose E2E;
5. зафиксируй:
   - количество Python и TypeScript файлов;
   - размер production frontend bundle;
   - количество тестов;
   - длительность основных CI jobs;
   - основные API endpoints;
   - активные background commands;
   - миграционные heads;
   - Compose services;
   - текущие публичные URL;
6. сохрани baseline в:

```text
docs/architecture/current-state-audit.md
```

Не начинай массовое удаление до понимания entrypoints и фактического поведения системы.

## 4.1.2. Найди мёртвый код

Проверь весь backend, frontend, scripts, infra и tests на:

- неиспользуемые файлы;
- неиспользуемые функции;
- неиспользуемые классы;
- неиспользуемые React-компоненты;
- неиспользуемые hooks;
- неиспользуемые exports;
- неиспользуемые API-функции;
- неиспользуемые типы;
- неиспользуемые зависимости;
- неиспользуемые environment variables;
- неиспользуемые Docker services;
- устаревшие Compose profiles;
- неиспользуемые migration helpers;
- старые seed/bootstrap scripts;
- дублирующиеся маршруты;
- недостижимые ветки;
- obsolete compatibility code;
- закомментированные большие блоки;
- временные debug helpers;
- тестовые заглушки, случайно оставшиеся в production;
- файлы, заменённые новой реализацией, но не удалённые;
- старые страницы, на которые больше нет routes;
- старые стили и CSS selectors;
- дублирующиеся assets;
- неиспользуемые npm и Python packages.

Для Python используй комбинацию:

```text
Ruff
Vulture или эквивалент
import graph
coverage
поиск runtime entrypoints
ручная проверка dynamic imports и CLI commands
```

Для TypeScript/React используй комбинацию:

```text
TypeScript compiler
ESLint
Knip или эквивалент
поиск routes
поиск lazy imports
поиск module manifests
bundle analysis
ручная проверка dynamic imports
```

Не удаляй код только потому, что один статический анализатор назвал его неиспользуемым.

Перед удалением проверь:

- импортируется ли он динамически;
- вызывается ли через CLI;
- используется ли Alembic;
- вызывается ли Docker command;
- используется ли worker;
- является ли plugin/adapter entrypoint;
- является ли public API;
- нужен ли для backward compatibility;
- используется ли тестами как часть реального контракта.

## 4.1.3. Классифицируй найденное

Для каждого подозрительного элемента выбери категорию:

```text
ACTIVE
GENERATED
COMPATIBILITY
DEPRECATED_BUT_REQUIRED
DEAD
DUPLICATE
NEEDS_REFACTOR
```

Создай audit ledger:

```text
docs/architecture/code-cleanup-audit.md
```

Для удаляемого кода укажи:

- путь;
- почему код мёртвый;
- чем это подтверждено;
- есть ли замена;
- какие тесты подтверждают безопасное удаление.

После завершения миграции ledger должен содержать полезную историю решений, а не список незакрытых обязательных задач.

## 4.1.4. Удали мёртвый код реально

Код категории `DEAD` и подтверждённые `DUPLICATE` должны быть удалены из репозитория.

Не оставляй:

```text
old/
legacy/
backup/
deprecated-copy/
component2.tsx
service_old.py
```

только из страха удалить их. Git уже хранит историю.

После удаления обязательно:

- удалить неиспользуемые зависимости;
- обновить imports;
- обновить tests;
- обновить Docker/CI/scripts;
- удалить лишние env variables;
- удалить obsolete documentation;
- пересобрать lockfiles;
- запустить полный regression.

## 4.1.5. Найди архитектурное дублирование

Ищи не только буквальные копии, но и повторяющиеся решения:

- два разных API transport;
- несколько способов обработки ошибок;
- несколько pagination contracts;
- несколько auth contexts;
- несколько permission helpers;
- несколько upload implementations;
- несколько health-check patterns;
- несколько worker loops;
- несколько вариантов outbox;
- несколько вариантов настройки SQLAlchemy;
- несколько способов загрузки server state;
- несколько однотипных UI-компонентов;
- несколько реализаций modal/table/pagination/filter state;
- одинаковые DTO и frontend types, поддерживаемые вручную;
- одинаковые Compose blocks;
- одинаковые CI steps.

Если логика инфраструктурная и действительно общая — вынеси её в platform SDK или frontend package.

Если логика бизнесовая — не объединяй её искусственно только из-за похожего кода.

## 4.1.6. Улучши плохие реализации

Во время миграции разрешено и требуется заменять технически слабые решения более качественными, если:

- поведение сохраняется;
- либо изменение поведения явно является исправлением дефекта;
- изменение покрыто тестами;
- сохранена совместимость публичного API либо добавлена миграция;
- решение проще поддерживать;
- отсутствует скрытая потеря данных.

Проверь минимум следующие зоны.

### Projects/PROM hardening

- Projects больше не является platform identity provider;
- Projects использует явные permissions и object-level policies;
- lifecycle проектов формализован;
- отклики, участники, задачи и отчёты защищены инвариантами и concurrency control;
- загрузка и скачивание файлов Projects соответствуют общему security/storage standard;
- Projects имеет audit/history и transactional notifications;
- критичные POST поддерживают idempotency;
- изменяемые сущности защищены optimistic concurrency;
- Projects PostgreSQL integration и E2E tests доведены до уровня Service Desk.

## Backend

- god services;
- длинные методы;
- смешивание HTTP, application и domain logic;
- транзакции внутри случайных repository methods;
- лишние `commit`;
- N+1 SQL queries;
- загрузка неограниченных коллекций;
- Python-фильтрация больших наборов вместо SQL;
- повторные запросы одной сущности;
- отсутствие индексов на реальные фильтры и foreign keys;
- небезопасные race conditions;
- отсутствие idempotency;
- неявные side effects;
- слишком широкие `except Exception`;
- потеря контекста ошибок;
- дублирование Pydantic schemas;
- ручное преобразование одних и тех же моделей;
- неправильные границы unit of work;
- синхронные тяжёлые операции внутри HTTP request;
- нестабильные worker loops;
- неоптимальная работа с файлами;
- отсутствие batch processing;
- неограниченная pagination;
- чрезмерно большие response payloads.

### Frontend

- огромные страницы и компоненты;
- business logic внутри JSX;
- повторяющиеся `useEffect` для загрузки данных;
- ручное кеширование;
- request waterfalls;
- повторные API-запросы;
- глобальные providers конкретного модуля;
- prop drilling;
- дублирующиеся forms;
- дублирующиеся tables/filters/modals;
- отсутствие lazy loading;
- импорт всего модуля в initial bundle;
- лишние rerenders;
- нестабильные dependencies hooks;
- хранение server state в глобальном client state;
- module-specific код внутри shared;
- неиспользуемый CSS;
- слишком большие bundles;
- ручные API types, расходящиеся с OpenAPI.

### Infrastructure

- огромный Compose без profiles;
- повторная сборка одинаковых слоёв;
- зависимости на `latest`;
- запуск seed при каждом production startup;
- отсутствие graceful shutdown;
- отсутствие resource limits/documented requests;
- лишние exposed ports;
- health check, не отличающий liveness от readiness;
- секреты в defaults;
- контейнеры под root;
- неоптимальные Docker layers;
- dev dependencies в runtime image;
- отсутствие `.dockerignore`;
- нестабильный порядок миграций;
- CI, запускающий всё без path filtering;
- повторная установка зависимостей в нескольких jobs без cache.

## 4.1.7. Оптимизация должна быть доказуемой

Не делай бессмысленные микрооптимизации.

Оптимизируй только там, где есть хотя бы одно основание:

- измерение;
- очевидная алгоритмическая проблема;
- N+1;
- лишний сетевой запрос;
- лишняя полная загрузка данных;
- блокирующая операция;
- большой bundle;
- повторное выполнение;
- высокая связанность;
- сложность, мешающая изменению кода.

Для важных улучшений зафиксируй до/после:

```text
SQL queries: 24 → 4
bundle: 1.8 MB → 950 KB
API requests on page load: 9 → 4
worker batch: 1 row → 50 rows
duplicate implementations: 3 → 1
service file: 650 lines → несколько сфокусированных компонентов
```

Добавь regression/performance tests для критичных оптимизаций.

## 4.1.8. Проверка базы данных

Проанализируй реальные SQLAlchemy queries и модели.

Проверь:

- индексы;
- unique constraints;
- foreign keys;
- cascade behavior;
- nullable fields;
- enum migration strategy;
- soft-delete filters;
- pagination;
- сортировки;
- конкурентные блокировки;
- transaction isolation assumptions;
- orphan records;
- duplicate records;
- timestamps/timezones;
- connection pool;
- statement timeouts.

Не добавляй индексы вслепую на каждое поле.

Добавляй индекс, если поле используется в:

- частом фильтре;
- JOIN;
- сортировке;
- unique lookup;
- worker polling;
- outbox selection.

Все изменения схемы оформляй Alembic migrations.

## 4.1.9. Проверка зависимостей

Для каждого package проверь:

- используется ли он;
- поддерживается ли он;
- не дублирует ли стандартную библиотеку или уже установленный package;
- нет ли нескольких библиотек для одной задачи;
- не попала ли dev dependency в runtime;
- зафиксирована ли версия;
- нет ли известных конфликтов;
- нужен ли `latest`.

Удаляй unused dependencies.

Для production dependencies не использовать плавающий `latest`.

Обновление major versions выполнять только при доказанной необходимости и с тестами.

## 4.1.10. Упростить, а не переусложнить

Не создавай абстракцию с единственной реализацией без понятной причины.

Не создавай:

- repository поверх repository;
- service поверх service без ответственности;
- generic base class для несвязанных сущностей;
- универсальную фабрику CRUD;
- event bus, который только вызывает функцию в том же файле;
- DI container сложнее самого приложения;
- десятки DTO для простой операции;
- отдельный микросервис для одной таблицы.

Каждая новая абстракция должна решать конкретную проблему:

- тестируемость;
- заменяемость интеграции;
- граница модуля;
- повторное инфраструктурное использование;
- контроль транзакции;
- безопасность;
- observability.

## 4.1.11. Quality gate после каждого этапа

После каждого крупного этапа выполняй:

```text
format
lint
type check
unit tests
integration tests
architecture checks
frontend build
affected E2E
```

После завершения всей миграции:

```text
full PostgreSQL integration
full Docker Compose E2E
dead-code scan
unused-dependency scan
bundle analysis
security scan
```

Нельзя считать этап завершённым, если новая структура создана, но старый дублирующий код оставлен рядом.


# 5. Целевая структура репозитория

Приведи репозиторий к следующему виду:

```text
prom/
├── apps/
│   ├── platform-shell/
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── modules/
│   │   │   └── shared/
│   │   ├── public/
│   │   ├── tests/
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   └── Dockerfile
│   │
│   ├── access-service/
│   │   ├── src/access_service/
│   │   │   ├── api/
│   │   │   ├── application/
│   │   │   ├── domain/
│   │   │   ├── infrastructure/
│   │   │   └── bootstrap/
│   │   ├── migrations/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   ├── projects/
│   │   ├── backend/
│   │   │   ├── src/projects/
│   │   │   ├── migrations/
│   │   │   ├── tests/
│   │   │   ├── pyproject.toml
│   │   │   └── Dockerfile
│   │   └── frontend/
│   │       ├── manifest.ts
│   │       ├── routes.tsx
│   │       ├── pages/
│   │       ├── features/
│   │       ├── entities/
│   │       └── api/
│   │
│   └── service-desk/
│       ├── backend/
│       │   ├── src/service_desk/
│       │   ├── migrations/
│       │   ├── workers/
│       │   ├── tests/
│       │   ├── pyproject.toml
│       │   └── Dockerfile
│       └── frontend/
│           ├── manifest.ts
│           ├── routes.tsx
│           ├── pages/
│           ├── features/
│           ├── entities/
│           └── api/
│
├── packages/
│   ├── python/
│   │   └── platform-sdk/
│   │       ├── src/platform_sdk/
│   │       │   ├── auth/
│   │       │   ├── rbac/
│   │       │   ├── config/
│   │       │   ├── errors/
│   │       │   ├── observability/
│   │       │   ├── health/
│   │       │   ├── outbox/
│   │       │   └── testing/
│   │       ├── tests/
│   │       └── pyproject.toml
│   │
│   ├── frontend/
│   │   ├── ui/
│   │   ├── auth/
│   │   ├── api-client/
│   │   ├── module-sdk/
│   │   ├── config/
│   │   └── test-utils/
│   │
│   └── contracts/
│       ├── access.openapi.json
│       ├── projects.openapi.json
│       ├── service-desk.openapi.json
│       └── generated/
│
├── infra/
│   ├── gateway/
│   │   └── nginx.conf
│   ├── compose/
│   │   ├── compose.yaml
│   │   ├── compose.local.yaml
│   │   └── compose.test.yaml
│   ├── monitoring/
│   ├── deployment/
│   └── sso-mock/
│
├── tools/
│   ├── dev/
│   ├── ci/
│   ├── architecture/
│   └── generators/
│
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── development/
│   └── operations/
│
├── pyproject.toml
├── package.json
├── pnpm-workspace.yaml
├── compose.yaml
├── dev.sh
├── dev.cmd
└── README.md
```

Допускается разумно скорректировать имена, но сохранить продуктовую группировку:

```text
apps/<module>/backend
apps/<module>/frontend
```

---

# 6. Этап 1. Безопасное перемещение текущего кода

Сначала выполни структурную миграцию без изменения поведения:

```text
backend/
→ apps/projects/backend/

service-desk-backend/
→ apps/service-desk/backend/

frontend/
→ apps/platform-shell/
```

При этом frontend-код Projects и Service Desk затем должен быть логически перемещён внутрь:

```text
apps/projects/frontend/
apps/service-desk/frontend/
```

Platform shell должен содержать только:

- корневую инициализацию;
- глобальные providers;
- layout;
- routing composition;
- landing/portal;
- профиль;
- platform navigation;
- error boundaries;
- module registry.

Обнови:

- Dockerfile paths;
- Compose build contexts;
- CI working directories;
- dev scripts;
- import paths;
- tsconfig aliases;
- Alembic paths;
- seed commands;
- тестовые команды;
- README.

После этого этапа все тесты должны проходить.

---

# 7. Этап 2. Frontend module-first architecture

## 7.1. Platform shell

Создай frontend module registry.

Контракт модуля:

```ts
export type PlatformModuleManifest = {
  id: string;
  title: string;
  description?: string;
  basePath: string;
  requiredPermissions: string[];
  icon?: React.ComponentType;
  loadRoutes: () => Promise<{ default: React.ReactNode }>;
  navigation: Array<{
    id: string;
    title: string;
    path: string;
    requiredPermissions?: string[];
  }>;
};
```

Каждый модуль экспортирует собственный manifest:

```ts
export const projectsManifest: PlatformModuleManifest = {
  id: "projects",
  title: "Проекты",
  basePath: "/projects",
  requiredPermissions: ["projects.access"],
  loadRoutes: () => import("./routes"),
  navigation: []
};
```

```ts
export const serviceDeskManifest: PlatformModuleManifest = {
  id: "service-desk",
  title: "Service Desk",
  basePath: "/service-desk",
  requiredPermissions: ["service_desk.access"],
  loadRoutes: () => import("./routes"),
  navigation: []
};
```

Platform shell:

- регистрирует manifests;
- показывает доступные модули;
- строит navigation;
- lazy-load routes;
- не импортирует каждую страницу вручную;
- не знает внутреннюю бизнес-структуру модулей.

## 7.2. Frontend boundaries

Запретить импорты:

```text
projects frontend → service-desk internal files
service-desk frontend → projects internal files
shared → module-specific files
```

Разрешить:

```text
module → packages/frontend/*
platform-shell → module manifest
```

Добавь ESLint/import boundary или собственную architecture check.

## 7.3. Server state

Добавь TanStack Query.

Используй единый QueryClient в platform shell.

У каждого модуля должны быть namespaced query keys:

```ts
["projects", ...]
["service-desk", ...]
["access", ...]
```

Убери module-specific side effects из общего API client.

Текущая инвалидация Service Desk counters не должна находиться в generic client.

Generic client должен только:

- делать запрос;
- добавлять auth context;
- нормализовать transport errors;
- возвращать typed result.

Инвалидация должна выполняться в mutation hooks конкретного модуля.

## 7.4. API clients

Создай отдельные API clients:

```text
packages/frontend/api-client
apps/projects/frontend/api
apps/service-desk/frontend/api
```

Общий transport:

```ts
createApiClient({
  baseUrl,
  getAccessToken,
  onUnauthorized,
  correlationIdProvider
});
```

Module API не должен вручную дублировать transport logic.

## 7.5. Auth provider

Убери зависимость глобального provider от Service Desk.

Должно быть:

```text
PlatformSessionProvider
AccessProvider
QueryClientProvider
RouterProvider
```

Service Desk-specific access data загружается только внутри Service Desk module либо как часть общего RBAC response.

---


# 7.6. Обязательная миграция frontend styling и дизайн-системы

Текущий глобальный CSS-файл на несколько тысяч строк является архитектурным дефектом. Нельзя просто перенести его в новую структуру или оставить как постоянный legacy layer.

Используй **самую новую стабильную версию Tailwind CSS, доступную на момент выполнения задачи**, с официальным Vite plugin. После установки зафиксируй реально разрешившуюся точную версию в `package.json` и lockfile. Не использовать `latest` в итоговых production dependencies.

Целевая styling-модель:

```text
Tailwind CSS
+
semantic design tokens
+
общий React UI-kit
+
CVA для variants
+
Radix Primitives для сложных доступных контролов
+
CSS Modules только для сложных локальных случаев
```

## Правила

1. Глобальный CSS содержит только:
   - Tailwind import;
   - reset/base;
   - semantic design tokens;
   - typography base;
   - минимальные platform-wide rules.
2. В глобальном CSS запрещены:
   - `.service-desk-*`;
   - `.projects-*`;
   - стили отдельных страниц;
   - module-specific responsive rules;
   - feature-specific selectors.
3. Не заменять один огромный CSS на огромные строки utilities в каждом JSX.
4. Повторяющиеся визуальные элементы оформить компонентами:
   - Button;
   - Input;
   - Select;
   - Textarea;
   - Checkbox;
   - Switch;
   - Dialog;
   - Popover;
   - Tabs;
   - Card/Panel;
   - Badge;
   - Table;
   - FormField;
   - EmptyState;
   - Spinner;
   - Pagination;
   - PageLayout.
5. Варианты компонентов реализовать через CVA или эквивалент:
   - intent;
   - size;
   - state;
   - density.
6. Для Dialog, Popover, Dropdown, Tabs, Tooltip, Select и других сложных интерактивных контролов использовать Radix Primitives либо эквивалентные доступные headless primitives.
7. CSS Modules допускаются только для:
   - сложных grid/layout;
   - календарей;
   - sticky tables;
   - drag-and-drop;
   - print styles;
   - нестандартных animations;
   - сложных псевдоэлементов.
8. Запретить:
   - `!important` без документированной причины;
   - произвольные hex-цвета вне tokens;
   - бесконтрольные arbitrary values;
   - динамическую конкатенацию Tailwind class names;
   - копии общего компонента внутри модулей;
   - добавление новых правил в legacy CSS.
9. Мигрировать вертикальными срезами:
   - страница;
   - компоненты;
   - responsive;
   - states;
   - visual regression;
   - удаление старых selectors.
10. Не оставлять старую и новую styling-системы параллельно после завершения миграции.
11. Итоговый global stylesheet должен быть небольшим и platform-only.
12. Добавить проверки:
   - unused CSS;
   - Tailwind class detection;
   - visual regression;
   - desktop/mobile screenshots;
   - accessibility states;
   - bundle CSS size.

Зафиксировать метрики до/после:

```text
global CSS lines
generated CSS size
unused selectors
initial CSS bundle
количество duplicate UI patterns
```



# 7.7. Обязательный frontend/platform hardening audit

Помимо CSS, проверь и исправь следующие риски текущего репозитория.

## Зависимости

- удалить `latest` из production и dev dependencies;
- использовать точные или контролируемые semver ranges;
- lockfile обязателен;
- обновление major versions — только с тестами;
- добавить Renovate или Dependabot с группировкой обновлений;
- удалить unused packages.

## Frontend quality tooling

Добавить:

```text
ESLint
Prettier
TypeScript strict mode
Knip или эквивалент
dependency boundary checks
bundle analyzer
accessibility checks
visual regression
```

CI должен падать при:

- unused exports;
- module boundary violation;
- TypeScript errors;
- lint errors;
- неожиданном росте bundle сверх установленного budget;
- оставшемся module-specific CSS в global layer.

## Router и module loading

- общий router не должен импортировать все страницы платформы напрямую;
- routes каждого модуля lazy-loaded;
- добавить module-level ErrorBoundary;
- добавить Suspense/loading state;
- неизвестный/недоступный модуль обрабатывается единообразно;
- navigation строится из module manifests.

## Server state

- не хранить server state вручную через повторяющиеся `useEffect/useState`;
- использовать TanStack Query;
- определить query key factories каждого модуля;
- отменять устаревшие запросы;
- предотвращать request waterfalls;
- настроить controlled retries;
- mutation invalidation находится внутри модуля;
- generic API client не знает о Service Desk counters или других module-specific эффектах.

## Forms

Провести аудит форм и выбрать единый подход:

```text
React Hook Form
+
schema validation, совместимая с API contracts
```

Не переписывать простые формы ради библиотеки, но убрать повторяющиеся ручные:

- touched state;
- field errors;
- submit state;
- reset;
- dirty tracking;
- nested dynamic arrays.

## Огромные компоненты

Найти:

- страницы на сотни строк;
- компоненты, содержащие несколько независимых редакторов;
- смешивание API/state/layout/form logic;
- повторяющиеся modal/list/editor patterns.

Разделить по ответственности, но не создавать искусственную файловую дробь.

## API contracts

- frontend types не поддерживаются вручную параллельно с Pydantic;
- генерировать TS types/client из OpenAPI;
- единый error contract;
- API versioning;
- contract drift check в CI.

## Авторизация

- platform provider не монтирует provider конкретного модуля глобально;
- UI permission checks не считаются защитой;
- backend проверяет все права;
- единый principal/session contract;
- object-level policies остаются в модулях;
- не хранить token в небезопасном постоянном storage после перехода на SSO, если возможна HttpOnly session model.

## Backend god files

Найти и разделить:

- services на сотни строк;
- router files, знающие несколько доменов;
- repository с бизнес-решениями;
- модели/схемы/маппинг в одном файле;
- giant admin pages и editors.

## Database/runtime

- основная интеграционная проверка должна работать на PostgreSQL, а не полагаться только на SQLite;
- seed/demo data не должны быть обязательным production startup step;
- миграции и seed разделить;
- production startup не должен автоматически создавать демо-пользователей;
- добавить backup/restore и migration rollback/runbook;
- добавить connection pool settings и statement timeout;
- проверить индексы, N+1 и pagination.

## Security

- убрать default production secrets;
- production mode должен падать с небезопасной конфигурацией;
- security headers;
- CSRF strategy для cookie session;
- rate limiting на чувствительные endpoints;
- upload MIME/signature validation;
- антивирусный integration port для файлов;
- audit log для RBAC и административных действий;
- dependency scanning;
- secret scanning.

## Observability

- structured JSON logs;
- correlation/request ID;
- OpenTelemetry-ready traces;
- Prometheus metrics;
- worker heartbeat;
- outbox lag;
- DB pool metrics;
- frontend error reporting adapter;
- module-level dashboards/runbooks.

## Production delivery

- multi-stage Docker images;
- dev dependencies не попадают в runtime;
- non-root containers;
- pinned base image strategy;
- `.dockerignore`;
- image vulnerability scan;
- immutable tags;
- graceful shutdown;
- readiness и liveness разделены;
- Compose только для local/test, production manifests отделены;
- ресурсные requests/limits задокументированы.

## Quality budgets

Установить и проверять budgets:

```text
global CSS size
initial JS bundle
module lazy chunk size
maximum file size warning
maximum function complexity warning
API request count for key pages
SQL query count for key scenarios
```

Превышение budget не всегда должно автоматически ломать сборку на первом этапе, но должно быть видно в CI. После baseline установить реальные пороги и включить blocking gate для критичных показателей.


# 8. Этап 3. Access/RBAC service

Создай отдельный `access-service`.

Это не identity provider и не замена SSO.

Он отвечает за:

- внутренний platform user;
- привязку к внешнему SSO subject;
- module access;
- roles;
- permissions;
- user-role assignments;
- group-role assignments;
- аудит изменения прав;
- выдачу frontend списка доступных модулей;
- backend service authorization context.

## 8.1. Модель данных

Минимальные таблицы:

```text
platform_users
modules
roles
permissions
role_permissions
user_role_assignments
groups
group_memberships
group_role_assignments
access_audit_events
```

Пример platform user:

```text
id
external_subject
email
display_name
department
position
is_active
last_login_at
created_at
updated_at
```

Пример permission:

```text
projects.access
projects.manage
service_desk.access
service_desk.assign
service_desk.approve
service_desk.manage_catalog
service_desk.manage_sla
```

## 8.2. API Access Service

Добавь:

```text
GET /api/v1/session
GET /api/v1/me
GET /api/v1/me/modules
GET /api/v1/me/permissions
GET /api/v1/admin/users
GET /api/v1/admin/users/{id}
PUT /api/v1/admin/users/{id}/roles
GET /api/v1/admin/roles
POST /api/v1/admin/roles
PATCH /api/v1/admin/roles/{id}
GET /health/live
GET /health/ready
```

`GET /api/v1/session` должен возвращать:

```json
{
  "user": {
    "id": "...",
    "external_subject": "...",
    "email": "...",
    "display_name": "..."
  },
  "modules": [
    {
      "id": "projects",
      "permissions": ["projects.access"]
    },
    {
      "id": "service-desk",
      "permissions": [
        "service_desk.access",
        "service_desk.assign"
      ]
    }
  ]
}
```

## 8.3. Центральный RBAC и локальные policies

Access Service отвечает только за общие permissions.

Модули продолжают проверять object-level policies.

Пример:

```python
require_permission(principal, "service_desk.assign")
TicketPolicy.require_assignable(principal, ticket)
```

Не выноси в Access Service:

- статусы заявок;
- участников проектов;
- конкретных согласующих;
- проверку владельца объекта;
- domain workflow rules.

## 8.4. Миграция текущих ролей

Сохрани совместимость с текущими ролями:

```text
employee
project_manager
platform_admin
service_desk_manager
service_desk_admin
```

Создай migration mapping в новые permissions.

`platform_admin` должен получать полный platform access.

Service Desk local capabilities должны продолжать работать.

На переходный период допускается adapter:

```text
Access Service permissions
+
Service Desk local capabilities
```

Затем дублирование постепенно устраняется.

---

# 9. Этап 4. SSO-ready authentication

Реальных параметров SSO может не быть.

Поэтому реализуй интерфейс:

```python
class IdentityProvider(Protocol):
    def authenticate_request(self, request) -> ExternalPrincipal: ...
    def build_login_redirect(self, return_url: str) -> str: ...
    def handle_callback(self, request) -> ExternalPrincipal: ...
    def build_logout_redirect(self, return_url: str) -> str: ...
```

Реализации:

```text
LocalMockIdentityProvider
TrustedHeaderIdentityProvider
OidcIdentityProvider
```

## 9.1. Local mock

Для локальной разработки:

```text
/auth/mock/login
/auth/mock/logout
```

Выбор тестового пользователя:

- employee;
- project manager;
- Service Desk manager;
- Service Desk admin;
- platform admin.

Mock должен выдавать такой же principal contract, как будущий SSO.

## 9.2. Trusted header adapter

Для окружения, где reverse proxy сам прошёл SSO:

```text
X-Forwarded-User
X-Forwarded-Email
X-Forwarded-Name
X-Forwarded-Department
```

Разрешать trusted headers только от доверенного gateway/network.

Не доверять этим headers при прямом публичном доступе.

## 9.3. OIDC adapter

Подготовь конфигурацию:

```text
SSO_PROVIDER=oidc
SSO_ISSUER_URL
SSO_CLIENT_ID
SSO_CLIENT_SECRET
SSO_REDIRECT_URI
SSO_SCOPES
SSO_JWKS_CACHE_TTL
SSO_ALLOWED_AUDIENCES
SSO_POST_LOGOUT_REDIRECT_URI
```

Не придумывай production URL.

При отсутствии реальных параметров adapter должен быть полностью реализован, но disabled.

## 9.4. Токены

Не используй Projects как issuer для всей платформы.

Для внутреннего взаимодействия используй переходную схему:

```text
SSO/mock
→ Access Service
→ short-lived internal platform token
→ module backend
```

Используй асимметричную подпись:

```text
RS256 или ES256
```

Предусмотри:

- `kid`;
- JWKS endpoint;
- key rotation;
- audience;
- issuer;
- expiration;
- clock skew;
- correlation ID.

Claims:

```json
{
  "iss": "prom-access",
  "sub": "platform-user-id",
  "external_sub": "utmn-subject",
  "aud": ["projects", "service-desk"],
  "permissions": ["..."],
  "iat": 0,
  "exp": 0,
  "jti": "..."
}
```

Не хранить пароли внутри PROM.

---

# 10. Этап 5. Общий Python Platform SDK

Создай устанавливаемый workspace package:

```text
packages/python/platform-sdk
```

Перенеси туда только инфраструктурные примитивы.

## Auth

- `CurrentPrincipal`;
- проверка internal JWT;
- JWKS client;
- permission dependency;
- service-to-service principal;
- request auth context.

## Config

- common environment settings;
- environment validation;
- secret validation;
- production safeguards.

## Errors

- domain/application error base;
- единый Problem Details response;
- correlation ID in error response.

## Observability

- JSON logging;
- request ID;
- trace ID;
- user ID;
- service name;
- module name;
- structured events.

## Health

- liveness;
- readiness;
- DB check;
- storage check;
- worker heartbeat.

## Outbox

- базовые модели;
- idempotency helpers;
- worker primitives;
- retry policy;
- `FOR UPDATE SKIP LOCKED`.

## Testing

- principal factories;
- test app helpers;
- PostgreSQL fixtures;
- contract test helpers.

Запретить перенос бизнес-сущностей в SDK.

Не должно быть:

```text
Project
Ticket
Approval
SLA policy
общий бизнес Status
```

---

# 11. Этап 6. Backend architecture каждого модуля

Projects и Service Desk должны использовать одинаковые архитектурные соглашения.

Целевая структура:

```text
src/<module>/
├── api/
│   ├── router.py
│   ├── dependencies.py
│   ├── schemas/
│   └── error_mapping.py
├── application/
│   ├── commands/
│   ├── queries/
│   ├── services/
│   ├── dto/
│   └── ports/
├── domain/
│   ├── entities/
│   ├── value_objects/
│   ├── policies/
│   ├── events/
│   ├── repositories/
│   └── errors.py
├── infrastructure/
│   ├── persistence/
│   │   ├── orm/
│   │   ├── repositories/
│   │   └── unit_of_work.py
│   ├── storage/
│   ├── messaging/
│   └── integrations/
└── bootstrap/
    ├── app.py
    ├── config.py
    └── container.py
```

Не нужно механически разносить каждый CRUD по 20 файлам.

Используй здравый баланс.

## Правила

```text
API → Application → Domain
Infrastructure implements Application/Domain ports
```

Domain не импортирует:

- FastAPI;
- HTTPException;
- Request;
- APIRouter;
- SQLAlchemy Session;
- конкретное файловое хранилище.

API не содержит бизнес-логику.

Repository не принимает бизнес-решения.

Application слой управляет транзакциями.

## Projects

Раздели текущий крупный ProjectService минимум на:

```text
ProjectCommandService
ProjectQueryService
ProjectMembershipService
ProjectRecommendationService
ProjectReportService
```

Либо эквивалентные use-case handlers.

Не меняй внешний API без необходимости.

## Service Desk

Не ломай существующие доменные границы.

Сохрани модули:

- tickets;
- templates;
- catalog;
- approvals;
- routing;
- SLA;
- notifications;
- access;
- attachments;
- workbench.

Приведи их к общему layout постепенно.

---


# 11.1. Обязательные backend production gates

Следующие требования являются обязательными для всех backend-приложений и общих Python packages.

## Воспроизводимые Python-сборки

Используй `uv` как единый инструмент управления Python workspace, зависимостями и lockfile, если аудит не выявит критическую несовместимость.

Требуется:

```text
root pyproject.toml
uv workspace
uv.lock
uv sync --frozen
```

Правила:

- `pyproject.toml` хранит осмысленные ограничения версий;
- `uv.lock` коммитится;
- CI и Docker используют frozen lockfile;
- production image не устанавливает dev dependencies;
- не использовать плавающие `latest`;
- отдельные backend не должны иметь независимо разрешившиеся несовместимые версии общих библиотек;
- обновления зависимостей проходят тесты и dependency scan.

## Запрет HTTP-зависимостей внутри Domain/Application

В слоях `domain` и `application` запрещены импорты:

```text
FastAPI
APIRouter
Request
Response
HTTPException
status
```

Бизнес-код выбрасывает собственные типизированные ошибки:

```text
ProjectNotFound
PermissionDenied
InvalidProjectTransition
TicketAlreadySubmitted
AssigneeUnavailable
VersionConflict
```

API layer преобразует их в единый HTTP error contract.

Workers, CLI и event consumers используют те же application use cases без FastAPI-specific поведения.

## Единый error contract

Используй единый Problem Details-compatible формат:

```json
{
  "type": "https://prom/errors/version-conflict",
  "title": "Конфликт версии",
  "status": 409,
  "detail": "Объект был изменён другим пользователем",
  "code": "VERSION_CONFLICT",
  "request_id": "...",
  "errors": [
    {
      "field": "title",
      "code": "required",
      "message": "Заполните поле"
    }
  ]
}
```

Frontend не должен определять тип ошибки по русскому тексту.

Код ошибки стабилен и пригоден для:

- frontend;
- audit;
- metrics;
- contract tests;
- внешних интеграций.

## Unit of Work и транзакционные границы

Правило:

```text
один application use case
=
одна транзакционная граница
```

Repository:

- читает;
- блокирует;
- добавляет;
- изменяет;
- удаляет;
- выполняет `flush` при необходимости.

Repository не выполняет финальный `commit` бизнес-сценария.

Вложенные domain/application services не должны независимо коммитить одну операцию по частям.

Введи практичный Unit of Work поверх SQLAlchemy без чрезмерно универсальных generic abstractions.

Критические операции должны быть атомарны:

```text
бизнес-изменение
+
history/audit
+
outbox event
+
snapshot
```

## Идемпотентность

Добавь idempotency для критичных команд:

- создание и отправка заявки;
- принятие решения согласующим;
- создание проекта;
- подача отклика;
- добавление участника;
- публикация формы;
- назначение роли;
- загрузка метаданных файла;
- внешние callbacks;
- webhooks;
- outbox consumers.

Для внешних POST-команд предусмотри `Idempotency-Key` там, где повтор запроса реалистичен.

Используй:

- unique constraints;
- command result table или equivalent store;
- stable event IDs;
- deduplication consumers.

Повторный запрос не создаёт второй бизнес-объект и возвращает предсказуемый результат.

## Конкурентное редактирование

Для административных и совместно редактируемых сущностей реализуй optimistic concurrency:

```text
version integer
или
ETag / If-Match
```

Объекты:

- проекты;
- настройки проекта;
- роли;
- шаблоны;
- SLA;
- маршрутизация;
- согласования;
- каталоги;
- будущие module settings.

При конфликте:

```text
409 Conflict
```

Нельзя молча перетирать изменения другого администратора.

Для строгих последовательных операций использовать row locks только там, где это оправдано.

## Zero-downtime migrations

Все production migrations должны использовать expand/contract подход.

Запрещено одним релизом:

- удалять используемую колонку;
- переименовывать колонку без compatibility phase;
- добавлять обязательную колонку без default/backfill strategy;
- менять enum несовместимым способом;
- выполнять длительный блокирующий backfill внутри обычной startup migration;
- удалять таблицу, пока старый код ещё может к ней обращаться.

Требуется:

```text
expand
→ compatible code
→ backfill
→ switch reads/writes
→ verification
→ contract in later release
```

Добавь migration tests на чистой PostgreSQL и upgrade from previous supported schema.

## Не переводить всё на async без причины

Не выполнять массовый переход на `AsyncSession` и async ORM только ради современности.

Сначала измерить:

- DB wait;
- external I/O;
- thread pool saturation;
- request latency;
- worker blocking.

Синхронный SQLAlchemy допустим при правильных запросах, pool settings и вынесенных workers.

Переход на async разрешён только при доказанной пользе и полном наборе regression tests.

## PostgreSQL как источник истины

SQLite допускается для быстрых unit tests, которые не зависят от поведения СУБД.

Обязательные тесты на PostgreSQL:

- migrations;
- repositories;
- constraints;
- JSON/array fields;
- concurrency;
- locks;
- outbox;
- idempotency;
- optimistic concurrency;
- numbering/sequences;
- transactional workflows.

## SQLAlchemy и запросы

Проведи аудит:

- N+1;
- лишних повторных SELECT;
- eager/lazy loading;
- pagination;
- сортировок;
- индексов;
- ограничений;
- transaction scope;
- connection leaks;
- long-running transactions;
- full table scans;
- загрузки неограниченных коллекций в Python.

Настрой:

```text
pool_size
max_overflow
pool_timeout
pool_recycle
pool_pre_ping
statement_timeout
application_name
```

API и workers могут иметь разные pool profiles.

Не допустить суммарного превышения лимита PostgreSQL соединений всеми модулями.

## Межсервисные HTTP-вызовы

Для каждого вызова другого сервиса обязательны:

- connect timeout;
- read timeout;
- ограниченный retry;
- retry только безопасных/idempotent операций;
- correlation ID;
- service authentication;
- contract test;
- понятная деградация;
- отсутствие бесконечных цепочек вызовов.

Запрещён распределённый монолит:

```text
request
→ service A
→ service B
→ service C
→ service D
```

Предпочитать локальные данные, события и асинхронную синхронизацию для нестрогих зависимостей.

## Access Service availability и отзыв прав

Модули не должны делать online RPC в Access Service на каждый обычный запрос.

Модель:

- короткоживущий подписанный platform token;
- локальная проверка signature/audience/expiry;
- JWKS cache;
- token/session version;
- возможность немедленной блокировки чувствительных учётных записей;
- online-check только для особо чувствительных операций при необходимости.

При падении Access Service:

- валидные ранее выданные tokens продолжают работать до короткого expiry;
- новые сессии не создаются;
- неизвестные права не разрешаются;
- sensitive admin operations могут fail closed;
- обычные модули не падают полностью из-за постоянной зависимости от Access Service.

## Transactional outbox standard

Стандартизируй outbox:

```text
event_id
event_type
aggregate_type
aggregate_id
payload
status
attempts
next_attempt_at
locked_at
locked_by
processed_at
last_error
created_at
```

Обязательны:

- запись в той же транзакции, что бизнес-изменение;
- `FOR UPDATE SKIP LOCKED`;
- batch processing;
- exponential backoff;
- dead-letter state;
- idempotent consumer;
- backlog/age metrics;
- replay tooling;
- audit trail.

## Политика данных

Для каждой сущности определить:

- physical delete;
- soft delete;
- archive;
- retention period;
- anonymization;
- legal/business audit requirement;
- cascade behavior;
- file cleanup;
- restore capability.

Особенно:

- platform users;
- projects;
- responses;
- reports;
- tickets;
- comments;
- attachments;
- RBAC assignments;
- audit events.

Не использовать каскадное удаление бизнес-истории без явного решения.

## Audit log

Создай единый append-only audit contract.

Хранить:

```text
actor_user_id
external_subject
action
module
object_type
object_id
before
after
reason
request_id
source
created_at
```

Audit обязателен для:

- изменения ролей и permissions;
- выдачи/отзыва доступа;
- административных изменений;
- публикации шаблонов;
- изменения SLA/маршрутизации;
- назначения исполнителей;
- изменения состава проекта;
- архивации/восстановления;
- скачивания особо чувствительных файлов при необходимости.

Application logs не заменяют audit log.

## Backend quality budgets

После baseline введи предупреждения и затем blocking thresholds для:

```text
максимальный размер service/module файла
cyclomatic complexity
количество SQL queries в ключевом use case
максимальная pagination page size
длительность транзакции
outbox backlog age
worker batch duration
API p95 latency
```

Порог размера файла является сигналом для анализа, а не основанием механически дробить код.


# 11.2. Обязательное доведение Projects/PROM до уровня Service Desk

Текущий Projects backend функционально и архитектурно слабее Service Desk. Нельзя ограничиться переносом его в новую папку. Проведи отдельный аудит Projects и доведи его до тех же production standards, сохраняя существующее поведение.

## Новая доменная граница Projects

Projects должен стать самостоятельным bounded context и владеть только собственными данными:

- проекты;
- проектные роли;
- отклики;
- этапы;
- задачи;
- рабочие группы;
- компетенции проекта;
- отчёты;
- вложения Projects;
- project audit/history;
- project-specific notifications.

Projects не владеет глобальной аутентификацией и глобальным RBAC.

Пользователи идентифицируются стабильным `platform_user_id` из Access Service/SSO.

## RBAC Projects

Создай явную permission model.

Минимальный набор permissions:

```text
projects.access
projects.view_all
projects.create
projects.update_own
projects.update_any
projects.archive_own
projects.archive_any
projects.manage_members
projects.manage_responses
projects.manage_tasks
projects.manage_reports
projects.manage_settings
projects.admin
```

Роли являются конфигурацией наборов permissions, а не единственным источником решений.

Сохрани migration mapping:

```text
employee
project_manager
platform_admin
```

Пример:

```text
employee
→ projects.access
→ projects.respond
→ projects.view_own

project_manager
→ projects.access
→ projects.create
→ projects.update_own
→ projects.manage_members
→ projects.manage_responses
→ projects.manage_tasks
→ projects.manage_reports

platform_admin
→ все permissions
```

Точный набор скорректировать после аудита текущих сценариев.

## Object-level policies Projects

Одного RBAC недостаточно.

Projects сам проверяет:

- кто является руководителем проекта;
- кто является ответственным;
- кто входит в рабочую группу;
- кто может видеть черновик;
- кто может изменить конкретный проект;
- кто может обработать отклик;
- кто может изменить задачу;
- кто может подать отчёт;
- кто может видеть вложение;
- кто может архивировать и восстанавливать.

Использовать централизованные project policies, а не разрозненные `if role == ...` в routers/services.

Пример:

```python
require_permission(principal, "projects.update_own")
ProjectPolicy.require_can_update(principal, project)
```

## Lifecycle Projects

Формализуй state machine проекта.

Минимально проанализировать состояния:

```text
draft
active
paused
completed
archived
```

Для каждого перехода определить:

- кто имеет право;
- preconditions;
- side effects;
- audit event;
- domain event;
- доступность откликов;
- доступность задач;
- доступность отчётности;
- возможность восстановления.

Не разрешать произвольную запись `status` без lifecycle policy.

## Отклики и участники

Обеспечь инварианты:

- пользователь не подаёт несколько активных откликов на один проект;
- решение по отклику идемпотентно;
- принятый отклик и участник не создаются дважды;
- пользователь не добавляется в рабочую группу повторно;
- удаление участника не нарушает обязательного руководителя;
- конкурентное принятие отклика защищено constraint/lock;
- действия записываются в history/audit.

## Задачи Projects

Проведи аудит task module:

- explicit statuses;
- assignee policy;
- due dates;
- project membership checks;
- optimistic concurrency;
- pagination;
- audit;
- notifications;
- idempotency;
- attachment relation при необходимости.

Задачу нельзя назначить пользователю без допустимого участия/доступа, если бизнес-правило не разрешает иное.

## Отчётность Projects

Проведи аудит reports:

- кто создаёт;
- за какой период;
- можно ли редактировать после сдачи;
- уникальность отчёта за период;
- статусы draft/submitted/accepted/rejected при наличии бизнес-потребности;
- optimistic concurrency;
- history;
- attachment security;
- экспорт в worker для тяжёлых форматов.

Не выполнять тяжёлую генерацию файлов внутри HTTP request.

## Вложения Projects

Доведи Projects uploads до общего production storage standard.

Обязательные возможности:

```text
LocalFilesystemStorage
S3CompatibleStorage
```

Для каждого файла хранить:

```text
id
module
owner_type
owner_id
storage_key
original_name
safe_name
content_type_declared
content_type_detected
size_bytes
checksum
status
uploaded_by
created_at
deleted_at
```

Статусы:

```text
pending
quarantined
available
rejected
deleted
```

Обязательные проверки:

- максимальный размер;
- максимальное количество;
- allowlist типов;
- MIME;
- magic bytes/signature;
- checksum;
- path traversal;
- безопасное имя;
- отсутствие публичного исполнения;
- авторизация на скачивание;
- orphan cleanup;
- удаление storage object после подтверждённого удаления метаданных;
- audit для административного удаления.

Подготовить antivirus scanning port:

```python
class MalwareScanner(Protocol):
    def scan(object_ref) -> ScanResult: ...
```

Локально допускается безопасный mock/disabled scanner с явным статусом.

В production нельзя считать файл доступным до успешной политики проверки, если scanner включён.

Для S3:

- private bucket;
- короткоживущие signed URLs либо backend streaming;
- scoped object keys;
- отсутствие guessable public URLs.

## Notifications Projects

Если Projects имеет или получает уведомления, не создавать вторую слабую реализацию.

Использовать общий контракт уведомлений и transactional outbox:

- отклик создан;
- отклик принят/отклонён;
- пользователь добавлен в проект;
- назначена задача;
- приближается дедлайн;
- открыт отчётный период;
- отчёт принят/возвращён;
- проект изменил состояние.

Не отправлять email напрямую внутри бизнес-транзакции.

## History и audit Projects

Добавь project history для пользовательски значимых событий:

```text
project_created
project_updated
status_changed
member_added
member_removed
response_created
response_accepted
response_rejected
task_created
task_assigned
report_submitted
attachment_added
project_archived
project_restored
```

Разделить:

- пользовательскую историю объекта;
- security/admin audit.

## Projects API

Привести к:

```text
/api/projects/v1/*
```

Сохранить compatibility routes старых URL.

Добавить:

- единый pagination contract;
- фильтры с allowlist;
- стабильную сортировку;
- maximum limits;
- typed errors;
- OpenAPI-generated frontend client;
- ETag/version для изменяемых сущностей;
- idempotency для критичных POST;
- request IDs.

## Projects database

Проверить:

- индексы project status;
- manager/responsible fields;
- membership;
- responses;
- tasks;
- report periods;
- attachments owner;
- archive/deleted filters;
- unique constraints;
- timestamps with timezone;
- orphan rows;
- cascade behavior.

Провести query count tests для:

- списка проектов;
- карточки проекта;
- рекомендаций;
- кандидатов;
- рабочего пространства;
- административного списка.

Не выполнять рекомендационный matching через загрузку всей базы в Python, если объём делает это неприемлемым. Сначала измерить и перенести фильтрацию/поиск в БД или отдельный индекс при необходимости.

## Projects workers

Создать workers только при реальной потребности:

- notifications outbox;
- exports;
- cleanup orphan files;
- scheduled report periods;
- reminders;
- future search indexing.

Все workers следуют общему lifecycle и observability standard.

## Projects tests parity

Projects должен получить уровень проверок не ниже Service Desk.

Обязательны:

- unit tests domain policies;
- PostgreSQL repository tests;
- migrations test;
- RBAC matrix tests;
- object-level authorization tests;
- file upload/download security tests;
- concurrency tests откликов и участников;
- idempotency tests;
- optimistic concurrency tests;
- outbox tests;
- API contract tests;
- Playwright E2E ключевых ролей;
- audit tests;
- archive/restore tests.

Не считать Projects готовым только потому, что старые pytest проходят.

## Projects Definition of Done

Projects считается доведённым только если:

- он не выдаёт platform JWT;
- он не владеет глобальными ролями;
- user identity приходит через platform principal;
- RBAC и object policies разделены;
- uploads соответствуют общему storage/security standard;
- критичные операции атомарны и идемпотентны;
- есть audit/history;
- PostgreSQL tests покрывают реальные особенности;
- API contract сгенерирован;
- legacy identity/bootstrap код удалён;
- frontend Projects использует module manifest, Query и общий UI-kit;
- нет функционального отката.

# 12. Этап 7. Межмодульные границы

Запретить прямые импорты ORM моделей одного модуля в другой.

Запретить прямое чтение базы другого модуля.

Удалить архитектурную зависимость:

```text
Service Desk → Projects database
```

Текущий identity bootstrap, читающий Projects DB, должен быть заменён на:

```text
Access Service session/user sync
```

В local development seed Access Service должен создавать demo platform users, а модули должны ссылаться на стабильный platform user ID.

Межмодульное взаимодействие:

```text
REST API
domain/integration events
outbox
published contracts
```

Не делать распределённую транзакцию между модулями.

---

# 13. Этап 8. Базы данных

Каждый крупный модуль владеет своей базой:

```text
access_db
projects_db
service_desk_db
```

Будущие:

```text
module_3_db
module_4_db
module_5_db
```

В production они могут находиться в одном PostgreSQL cluster, но должны иметь:

- отдельную database;
- отдельного DB user;
- отдельный пароль;
- отдельные миграции;
- отсутствие cross-database access.

Запретить module backend подключаться с credentials другого модуля.

Добавь production-safe pool settings:

- pool size;
- max overflow;
- pool timeout;
- pool recycle;
- statement timeout;
- application name.

SQLite оставить только для быстрых unit tests там, где это оправдано.

Интеграционные и concurrency tests выполнять на PostgreSQL.

---

# 14. Этап 9. Gateway

Оставь Nginx как gateway, но приведи маршруты к стандарту:

```text
/api/access/v1/*
/api/projects/v1/*
/api/service-desk/v1/*
```

Frontend:

```text
/*
```

Gateway должен:

- проксировать API;
- задавать request ID, если его нет;
- передавать correlation headers;
- иметь body size limits;
- иметь timeout policies;
- скрывать внутренние backend ports;
- добавлять security headers;
- иметь `/healthz`.

Не переносить бизнес-авторизацию в Nginx.

Сохрани временную совместимость со старыми путями:

```text
/api/*
/service-desk-api/*
```

Добавь deprecation comments и compatibility routes.

---

# 15. Этап 10. Contracts и generated clients

Каждый backend публикует OpenAPI.

Добавь команды:

```text
generate:contracts
check:contracts
```

Генерируй TypeScript clients или типы из:

```text
access.openapi.json
projects.openapi.json
service-desk.openapi.json
```

Frontend module должен использовать generated contract types там, где это практично.

CI должен падать, если:

- backend contract изменён;
- generated client не обновлён;
- появился несовместимый breaking change без API version bump.

---

# 16. Этап 11. События и workers

Стандартизируй worker model.

Каждый worker:

- отдельная команда;
- отдельный process;
- graceful shutdown;
- heartbeat;
- structured logs;
- retries;
- exponential backoff;
- idempotency;
- batch limits;
- `FOR UPDATE SKIP LOCKED`, где нужен конкурентный polling;
- readiness/health state.

Service Desk:

- SLA worker;
- notification outbox worker.

Outbox worker должен запускаться постоянным сервисом, а не только ручной одноразовой командой.

Добавь:

```text
service-desk-notification-worker
```

В будущем модули смогут добавлять собственные workers по тому же шаблону.

Не добавлять Kafka без реальной необходимости.

Сейчас использовать PostgreSQL outbox.

Подготовить interface для будущего broker publisher.

---

# 17. Этап 12. Observability

Добавь во все backend и workers:

- JSON logs;
- `service`;
- `module`;
- `environment`;
- `request_id`;
- `trace_id`;
- `user_id`;
- `event`;
- `duration_ms`;
- `status_code`;
- exception type;
- DB operation context без SQL secrets.

Добавь OpenTelemetry-ready setup.

Если exporter не настроен, приложение продолжает работать.

Переменные:

```text
OTEL_ENABLED
OTEL_SERVICE_NAME
OTEL_EXPORTER_OTLP_ENDPOINT
OTEL_TRACES_SAMPLER
```

Добавь Prometheus-compatible `/metrics` либо подготовленный instrumentation endpoint.

Минимальные метрики:

- HTTP request count;
- HTTP latency;
- HTTP errors;
- DB pool state;
- worker iteration duration;
- worker failures;
- outbox pending count;
- SLA warnings;
- SLA breaches;
- module business operation counters.

Не логировать:

- JWT;
- cookies;
- passwords;
- secrets;
- содержимое приватных файлов;
- персональные данные без необходимости.

---

# 18. Этап 13. Storage

Создай общий storage port в platform SDK:

```python
class ObjectStorage(Protocol):
    def put(...): ...
    def get(...): ...
    def delete(...): ...
    def exists(...): ...
```

Реализации:

```text
LocalFilesystemStorage
S3CompatibleStorage
```

Текущий local volume режим сохранить.

Production-ready конфигурация:

```text
STORAGE_BACKEND=filesystem|s3
S3_ENDPOINT
S3_BUCKET
S3_ACCESS_KEY
S3_SECRET_KEY
S3_REGION
```

Модуль сам владеет своими объектными ключами.

Service Desk security checks на скачивание файлов сохранить.

---

# 19. Этап 14. Конфигурация и secrets

Добавь root `.env.example`.

Раздели переменные по префиксам:

```text
PLATFORM_
ACCESS_
PROJECTS_
SERVICE_DESK_
SSO_
OTEL_
S3_
```

В production режиме приложение должно падать при:

- дефолтном JWT/private key;
- пустом DB password;
- mock SSO provider;
- debug mode;
- небезопасном CORS wildcard с credentials;
- отсутствующем issuer/audience.

Не хранить production secrets в Git.

Добавь документацию по secrets.

---

# 20. Этап 15. Docker Compose

Root `compose.yaml` должен поддерживать profiles:

```text
core
projects
service-desk
full
test
```

Примеры:

```bash
docker compose --profile core --profile projects up --build
docker compose --profile core --profile service-desk up --build
docker compose --profile full up --build
```

`core`:

- gateway;
- platform shell;
- access-service;
- access-db;
- SSO mock.

`projects`:

- projects-db;
- projects migrations;
- projects seed;
- projects backend.

`service-desk`:

- service-desk-db;
- migrations;
- seed;
- backend;
- SLA worker;
- notification worker.

Полный локальный запуск должен оставаться одной командой:

```bash
./dev.sh up
```

Windows:

```powershell
.\dev.cmd up
```

Команды:

```text
up
down
reset
status
logs
test
test-unit
test-integration
test-e2e
generate-contracts
architecture-check
```

---

# 21. Этап 16. CI/CD

Перестрой GitHub Actions.

Добавь `detect-changes`.

Пути:

```text
apps/access-service/**
apps/projects/**
apps/service-desk/**
apps/platform-shell/**
packages/python/platform-sdk/**
packages/frontend/**
infra/**
```

Jobs:

```text
architecture-check
python-lint
python-type-check
platform-sdk-tests
access-service-tests
projects-tests
service-desk-tests
projects-postgres-integration
service-desk-postgres-concurrency
frontend-tests
frontend-build
contract-check
docker-build
module-e2e
full-stack-e2e
security-scan
```

Shared package changes запускают зависимые jobs всех модулей.

Добавь Ruff для всех Python packages.

Добавь type checking:

```text
mypy или pyright
```

Добавь frontend lint.

Добавь dependency scan:

```text
pip-audit
npm audit --omit=dev
```

Добавь Docker image scan, если возможно без нестабильности.

Docker images тегировать:

```text
commit SHA
```

Не использовать `latest` как единственный production tag.

---

# 22. Этап 17. Architecture tests

Добавь автоматические проверки:

1. Frontend shared не импортирует module internals.
2. Projects не импортирует Service Desk.
3. Service Desk не импортирует Projects.
4. Domain не импортирует FastAPI.
5. Domain не импортирует SQLAlchemy.
6. Module не импортирует private infrastructure другого module.
7. Platform SDK не импортирует business modules.
8. Access Service не импортирует module ORM.
9. Запрещены прямые подключения к чужим DB URL.
10. Запрещены циклические frontend module imports.

Сделай команду:

```bash
./dev.sh architecture-check
```

---

# 23. Этап 18. Generator нового модуля

Создай generator:

```bash
./dev.sh create-module documents
```

Он создаёт:

```text
apps/documents/backend
apps/documents/frontend
migrations
tests
Dockerfile
manifest
routes
health endpoints
README
Compose profile
CI path configuration
OpenAPI contract target
```

Новый модуль должен сразу иметь:

- стандартный backend bootstrap;
- platform SDK;
- auth principal;
- permission example;
- PostgreSQL config;
- Alembic;
- unit test;
- integration test;
- frontend route;
- lazy manifest;
- Query key factory;
- API client;
- health checks.

Generator не должен автоматически добавлять бизнес-логику.

---

# 24. Этап 19. Документация и ADR

Создай:

```text
docs/architecture/overview.md
docs/architecture/backend.md
docs/architecture/frontend.md
docs/architecture/auth-and-rbac.md
docs/architecture/data-ownership.md
docs/architecture/events.md
docs/architecture/observability.md
docs/development/local-development.md
docs/development/new-module.md
docs/operations/deployment.md
docs/operations/sso.md
docs/operations/backups.md
```

ADR:

```text
ADR-001-product-modules-as-bounded-services.md
ADR-002-monorepo.md
ADR-003-platform-shell.md
ADR-004-sso-and-access-service.md
ADR-005-central-rbac-local-policies.md
ADR-006-database-per-module.md
ADR-007-postgresql-outbox.md
ADR-008-no-microfrontends-yet.md
ADR-009-platform-sdk.md
ADR-010-api-versioning.md
```

В README покажи:

- архитектуру;
- список модулей;
- запуск;
- profiles;
- тесты;
- создание нового модуля;
- SSO mock;
- production variables.

---

# 25. Что запрещено

Не делай:

- один общий backend для всех будущих крупных модулей;
- десятки мелких микросервисов;
- одну общую бизнес-базу;
- cross-module SQL joins;
- прямое чтение Projects DB из Service Desk;
- общий `common/models.py` для Project и Ticket;
- самописный тяжёлый API Gateway;
- Kafka без необходимости;
- microfrontends сейчас;
- полное переписывание Service Desk;
- удаление рабочих тестов;
- отключение security checks;
- скрытие падающих тестов через skip;
- мок вместо production-кода без явной причины;
- передачу module-specific side effects в generic API client;
- хранение production secrets в репозитории;
- ожидание реальных SSO параметров перед выполнением миграции.
- механический перенос всего старого кода без анализа;
- сохранение мёртвого кода «на всякий случай»;
- создание каталогов `legacy`, `old`, `backup` вместо удаления;
- слепое удаление только по результату одного статического анализатора;
- преждевременную оптимизацию без причины;
- сохранение заведомо плохой реализации только ради минимального diff;
- новые универсальные абстракции без конкретной пользы;
- маскировку архитектурных проблем дополнительными слоями;
- оставление двух параллельных реализаций после завершения миграции;
- добавление индексов и кешей без понимания сценария использования;
- отключение lint/type/dead-code checks для прохождения CI.

---

# 26. Совместимость

Сохрани:

- текущие пользовательские сценарии;
- текущие демо-аккаунты через local SSO mock;
- текущие frontend URL;
- текущие старые API paths через compatibility proxy;
- существующие данные;
- миграционную историю;
- вложения;
- тесты;
- Docker Compose запуск.

Если изменяются URL, создай redirects или proxy aliases.

Если меняются package paths, обнови импорты автоматически и полностью.

Если меняются DB schemas, создай настоящие миграции.

Не выполнять destructive reset production данных.

---

# 27. Порядок выполнения без остановок

Выполняй последовательно:

```text
1. Аудит текущего дерева, entrypoints, runtime-команд и тестов
2. Фиксация baseline и текущих публичных контрактов
3. Поиск мёртвого кода, дублей, unused dependencies и проблем производительности
4. Создание architecture migration branch
5. Безопасное удаление подтверждённого мёртвого кода
6. Структурное перемещение каталогов
7. Исправление Compose/CI/scripts
8. Проверка полного тестового контура
9. Platform SDK
10. Access Service
11. SSO mock и auth abstraction
12. Удаление Service Desk → Projects DB зависимости
13. Frontend module registry
14. TanStack Query и API clients
15. Backend boundaries, Unit of Work и разделение god services
16. Отдельный Projects/PROM hardening: RBAC, policies, lifecycle, uploads, audit, outbox и PostgreSQL tests
17. Оптимизация SQL, API request flow, frontend bundle и workers
18. Gateway/API versioning
19. Workers/outbox standardization
20. Contracts
21. Observability
22. Architecture tests
23. Повторный dead-code и dependency audit
24. Module generator
25. Docs/ADR
26. Полный regression, PostgreSQL integration и production-like E2E
27. Финальная фиксация метрик до/после
```

Не спрашивай согласования между этапами.

Если находишь неоднозначность:

1. выбери наиболее безопасное production-ready решение;
2. зафиксируй его в ADR;
3. продолжай работу.

Если часть зависит от неизвестных параметров ТюмГУ:

1. реализуй интерфейс;
2. реализуй mock;
3. реализуй disabled OIDC adapter;
4. добавь `.env.example`;
5. продолжай остальные этапы.

---

# 28. Требования к коммитам

Делай логические коммиты:

```text
chore(repo): reorganize applications by product
feat(platform-sdk): add shared auth and observability primitives
feat(access): add centralized RBAC service
refactor(auth): decouple service desk from projects identity
refactor(web): add platform module registry
refactor(web): move server state to TanStack Query
feat(infra): add compose profiles and gateway routes
feat(contracts): generate typed API clients
ci: add affected module pipelines
docs(architecture): document target platform model
```

Не складывай всю миграцию в один нечитаемый commit.

---

# 29. Definition of Done

Работа считается завершённой только если:

## Очистка и качество

- проведён и задокументирован аудит текущего кода;
- подтверждённый мёртвый код удалён;
- unused Python и npm dependencies удалены;
- нет параллельных старой и новой реализаций одного механизма;
- module-specific код не остался в generic shared слоях;
- god services разделены по ответственности;
- устранены обнаруженные N+1 и лишние request waterfalls;
- критичные оптимизации подтверждены тестами или метриками;
- production bundle проанализирован;
- dead-code scan проходит;
- unused-dependency scan проходит;
- code-cleanup audit содержит объяснение значимых удалений;
- Git history используется вместо каталогов `old` и `backup`.

## Репозиторий

- структура соответствует продуктовой архитектуре;
- Projects и Service Desk находятся в `apps/`;
- есть `access-service`;
- есть `platform-sdk`;
- есть frontend module registry;
- есть generator нового модуля.

## Auth

- Projects больше не является identity provider платформы;
- Service Desk не читает Projects DB;
- local SSO mock работает;
- OIDC-ready adapter существует;
- RBAC централизован;
- object-level policies остаются локально.

## Projects/PROM hardening

- Projects больше не является platform identity provider;
- Projects использует явные permissions и object-level policies;
- lifecycle проектов формализован;
- отклики, участники, задачи и отчёты защищены инвариантами и concurrency control;
- загрузка и скачивание файлов Projects соответствуют общему security/storage standard;
- Projects имеет audit/history и transactional notifications;
- критичные POST поддерживают idempotency;
- изменяемые сущности защищены optimistic concurrency;
- Projects PostgreSQL integration и E2E tests доведены до уровня Service Desk.

## Backend

- каждый продукт имеет отдельный backend и DB ownership;
- common infrastructure вынесена;
- нет запрещённых cross-module imports;
- health/readiness работают;
- workers имеют стандартный lifecycle.

## Frontend

- один shell;
- lazy modules;
- navigation строится из manifests;
- server state использует TanStack Query;
- generic API client не зависит от Service Desk;
- Projects и Service Desk frontend логически изолированы.

## Infra

- Compose profiles работают;
- полный stack запускается одной командой;
- old URLs совместимы;
- gateway маршрутизирует versioned API;
- volumes сохраняются.

## CI

- все существующие тесты проходят;
- Ruff проходит для всех Python приложений;
- type checking проходит;
- frontend tests/build проходят;
- PostgreSQL tests проходят;
- E2E проходит;
- architecture checks проходят;
- contracts актуальны.

## Документация

- README обновлён;
- ADR созданы;
- описан новый модуль;
- описан SSO mock;
- описан будущий production SSO;
- описан RBAC;
- описан локальный запуск.

---

# 30. Финальный отчёт исполнителя

После завершения выдай:

1. краткое архитектурное резюме;
2. новое дерево репозитория;
3. список выполненных этапов;
4. список ключевых решений;
5. список compatibility mechanisms;
6. список миграций БД;
7. список новых env variables;
8. список тестов и их результаты;
9. список известных ограничений;
10. отчёт об очистке:
    - какие файлы и механизмы удалены;
    - почему они были признаны мёртвыми;
    - какие зависимости удалены;
    - какие дубли объединены;
11. отчёт об улучшениях:
    - какие слабые реализации заменены;
    - какие god services разделены;
    - какие SQL/API/frontend/worker оптимизации выполнены;
    - измерения до/после;
12. отдельный отчёт по Projects/PROM:
    - какие RBAC и object policies внедрены;
    - какие lifecycle/invariants формализованы;
    - как защищены uploads/downloads;
    - какие audit/history/outbox механизмы добавлены;
    - какие PostgreSQL/concurrency/E2E тесты добавлены;
13. backend production report:
    - lockfile и воспроизводимость сборок;
    - Unit of Work и транзакционные границы;
    - idempotency;
    - optimistic concurrency;
    - zero-downtime migration решения;
    - Access Service failure/revocation model;
14. точные команды:
    - запуск;
    - тесты;
    - запуск отдельного модуля;
    - создание нового модуля;
    - подключение реального SSO.

Не заканчивай отчёт предложением выполнить оставшуюся обязательную часть позже.

Обязательная архитектурная миграция должна быть выполнена в рамках задачи.

---

# 31. Приоритеты при конфликте требований

Приоритет:

```text
1. Сохранность данных и корректность бизнес-поведения
2. Безопасность
3. Удаление подтверждённого мёртвого и дублирующего кода
4. Простота и понятность итогового решения
5. Изоляция модулей
6. Удобство добавления новых модулей
7. Производительность подтверждённых проблемных мест
8. Локальная разработка
9. Автоматические тесты и наблюдаемость
10. Чистота структуры
11. Минимальный diff
```

При необходимости большего diff ради правильной устойчивой архитектуры делай больший diff, но не переписывай работающую бизнес-логику без причины.

---

# 32. Итоговая архитектурная формула

Результат должен соответствовать модели:

```text
Монорепозиторий
+
единый frontend platform shell
+
отдельный крупный сервис на каждый сложный бизнес-модуль
+
собственная база каждого модуля
+
SSO ТюмГУ как внешний Identity Provider
+
Access Service как центральный RBAC
+
локальные domain policies в модулях
+
общий Platform SDK
+
versioned API contracts
+
PostgreSQL outbox и workers
+
единые observability и CI standards
```

Начинай с текущего состояния `lekovvv-cmd/prom` и доведи репозиторий до этой архитектуры без дополнительных вопросов и промежуточных согласований.

Не завершай задачу после структурного перемещения каталогов. Обязательная часть включает реальное улучшение Projects/PROM, удаление его зависимости от собственной platform authentication, внедрение корректного RBAC/object policies, безопасных файлов, транзакционных границ, аудита, concurrency/idempotency и PostgreSQL-backed проверок.

Не оставляй пункты этого документа как TODO, если они входят в Definition of Done. Неизвестные внешние параметры допустимо закрыть adapter/interface/mock-конфигурацией, но внутренние архитектурные и security-требования должны быть реализованы.

