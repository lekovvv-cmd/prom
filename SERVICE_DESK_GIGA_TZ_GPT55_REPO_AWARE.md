# Техническое задание: Service Desk для платформы PROM / ШПИУ

> **Статус документа:** основной источник требований для реализации.
>
> **Целевая аудитория:** coding-agent GPT-5.5 и разработчики проекта.
>
> **Ключевое правило:** реализовать Service Desk полноценно в объёме функциональности, зафиксированной в данном ТЗ и референсных скриншотах. Нельзя самостоятельно упрощать, вырезать или переносить «на потом» подтверждённую функциональность.
>
> **Визуальное правило:** Service Desk должен быть выполнен в визуальном стиле существующей платформы `prom`. Скриншоты реального ServiceDesk используются как референсы поведения, состава экранов, полей, процессов и пользовательских сценариев, но **не как визуальный референс для копирования интерфейса ManageEngine**.

---

# 0. Инструкция агенту перед началом разработки

## 0.0. Правило первичного onboarding и повторного использования контекста

Полный onboarding по Service Desk выполняется только при первом входе агента в реализацию Service Desk либо если текущий агент не имеет достаточного контекста о проекте.

При первичном onboarding:

1. Прочитать этот файл полностью.
2. Проинспектировать текущий репозиторий `prom`.
3. Зафиксировать фактическую архитектуру backend и frontend.
4. Найти существующие:
   - механизм аутентификации;
   - JWT и auth dependencies;
   - структуру backend;
   - FSD-слои frontend;
   - общий API client;
   - UI-компоненты;
   - обработку ошибок;
   - механизм вложений;
   - конфигурацию PostgreSQL и Alembic;
   - Docker/Compose-конфигурацию;
   - тестовую инфраструктуру.
5. Просмотреть все изображения в папке:

```text
SERVICE_DESK_SCREENSHOTS/
```

Скриншоты являются реальными скриншотами используемого ServiceDesk и используются как функциональные референсы.

6. Составить внутреннее понимание соответствия:

```text
требование
→ backend часть
→ frontend часть
→ миграция
→ тест
→ связанный screenshot, если есть
```

После завершения первичного onboarding агент НЕ должен автоматически повторять полный onboarding перед каждым следующим Stage, feature slice или сообщением пользователя.

При продолжении работы в существующей задаче или при наличии уже реализованных предыдущих Stage агент должен:

1. проверить текущее состояние `main`;
2. прочитать `REPORT.md`;
3. определить текущий завершённый Stage и следующий Stage;
4. прочитать в этом ТЗ требования только текущего Stage;
5. дополнительно прочитать только непосредственно связанные разделы ТЗ;
6. просмотреть только непосредственно связанные с текущей функциональностью screenshots;
7. инспектировать только релевантные части backend/frontend и связанные существующие реализации.

Повторное полное чтение всего ТЗ, повторный просмотр всей папки `SERVICE_DESK_SCREENSHOTS` и полный аудит всего репозитория НЕ требуются, если:

- агент уже выполнил первичный onboarding в рамках текущей задачи;
- архитектура проекта радикально не изменилась;
- пользователь явно не запросил полный повторный аудит;
- обнаруженное противоречие не требует повторной проверки всех исходных требований.

Если агенту не хватает контекста для текущего Stage, он должен точечно открыть необходимые разделы ТЗ, файлы репозитория и screenshots, а не автоматически повторять полный onboarding.

При конфликте текущего состояния реализации с ранее изученным контекстом источником истины являются:

1. актуальный `main`;
2. `REPORT.md`;
3. требования текущего Stage в этом ТЗ;
4. связанные разделы ТЗ и screenshots.

Полный onboarding разрешается повторить только при объективной необходимости.

## 0.1. Запрет на самостоятельное упрощение

Функция не может быть исключена только потому, что:

- она сложная;
- требует дополнительных сущностей;
- не помещается в «быстрый MVP»;
- агент считает её избыточной;
- в текущей архитектуре её неудобно реализовать.

Если функция описана в ТЗ, она обязательна.

Если поведение невозможно однозначно определить:

1. не удалять функцию;
2. не заменять её упрощённой;
3. выбрать архитектуру, позволяющую реализовать полное поведение;
4. зафиксировать неоднозначность в `SERVICE_DESK_OPEN_QUESTIONS.md`;
5. реализовать подтверждённую часть без потери расширяемости.

## 0.2. Приоритет источников

При конфликте информации использовать следующий порядок:

1. это ТЗ;
2. фактическое поведение, видимое на скриншотах `SERVICE_DESK_SCREENSHOTS`;
3. существующая архитектура `prom`, если она не противоречит требованиям Service Desk;
4. архитектурные предположения разработчика.

Агент не должен молча придумывать новое бизнес-поведение.

## 0.3. Скриншоты — функциональный, а не визуальный референс

Скриншоты нужны для понимания:

- структуры каталога услуг;
- состава форм;
- обязательных полей;
- работы справочников;
- карточки заявки;
- утверждений;
- назначения специалиста;
- статусов;
- вложений;
- состава пользовательских действий.

Не копировать:

- старую визуальную стилистику ManageEngine;
- серо-синюю цветовую схему;
- расположение элементов один в один;
- устаревшие паттерны таблиц и форм;
- визуальный chrome исходной системы.

Service Desk должен выглядеть как родная часть `prom`.

---

## 0.4. Фактическая структура репозитория `prom`, подтверждённая перед подготовкой этой версии ТЗ

Эта версия ТЗ сверена с публичным `main` репозитория `lekovvv-cmd/prom`.

На момент подготовки документа фактическая структура платформы следующая:

```text
prom/
  backend/
    app/
      api/
      core/
      modules/
    alembic/
    scripts/
    tests/
    pyproject.toml

  frontend/
    src/
      app/
      pages/
      widgets/
      features/
      entities/
      shared/
    e2e/
    package.json

  SERVICE_DESK_SCREENSHOTS/

  docker-compose.yml
  dev.cmd
  dev.sh

  .github/
    workflows/
      ci.yml
```

### Подтверждённые факты о текущем backend

Текущий Projects backend:

- расположен в `backend/`;
- является одним FastAPI-приложением;
- подключает общий `api_router` с prefix `/api`;
- использует структуру `api / core / modules`;
- использует SQLAlchemy 2 и Alembic;
- использует PostgreSQL в development;
- использует SQLite в текущем CI для backend tests и E2E preparation;
- текущая авторизация находится внутри существующего backend;
- JWT содержит `sub` и `exp`;
- `sub` сейчас является UUID пользователя из текущей таблицы `users`;
- `CurrentUser` после decode JWT загружает `User` из текущего Projects backend;
- guards `require_admin` и `require_admin_or_manager` завязаны на `UserRole`;
- текущий `UserRole` содержит `employee`, `project_manager`, `admin`.

Следствие:

> Service Desk **нельзя** реализовывать через существующие `CurrentUser`, `AdminUser`, `StrictAdminUser` как готовую авторизационную модель Service Desk.

Их можно переиспользовать только как материал для понимания текущего auth flow.

Service Desk должен иметь собственный access policy и собственную локальную проекцию пользователя.

### Подтверждённые факты о текущем frontend

Frontend:

- расположен в `frontend/`;
- уже использует Feature-Sliced Design;
- entrypoint: `frontend/src/app/main.tsx`;
- маршруты находятся в `frontend/src/app/routes/AppRouter.tsx`;
- auth context находится в `frontend/src/app/providers/AppProviders.tsx`;
- существующие guards `AdminRoute` и `ManagerRoute` завязаны на Projects roles;
- используется один `apiClient`;
- текущий API URL читается из `VITE_API_BASE_URL`;
- токен хранится в localStorage;
- `Header` и текущая навигация находятся в `frontend/src/widgets/header/ui/Header.tsx`;
- shared UI уже содержит переиспользуемые primitives;
- основной визуальный язык задан в `frontend/src/app/styles/globals.css`.

Следствие:

> Service Desk должен расширять **существующий frontend и существующий FSD**, а не создавать новый `apps/web` и не переносить весь frontend в новую монорепозиторную структуру.

### Подтверждённые факты о текущем CI

`.github/workflows/ci.yml` уже запускается:

```text
on push: branches ["**"]
on pull_request
```

И выполняет:

```text
backend pytest

frontend vitest
frontend build

Playwright browser E2E
```

Следствие:

> Git workflow Service Desk должен использовать уже существующую модель CI и расширить её отдельной проверкой нового Service Desk backend. Не создавать вторую параллельную CI-систему.

### Правило адаптации ТЗ

Если ниже в ТЗ приведена примерная структура, агент должен адаптировать её к подтверждённой структуре выше.

Не выполнять массовый repository refactor только ради соответствия красивой схеме из документа.

Service Desk должен быть архитектурно изолирован, но существующие Projects backend и frontend не нужно переносить без отдельной необходимости.


---

# 1. Контекст платформы

Существующая платформа `prom` уже содержит проектный модуль ШПИУ.

Текущий проектный контекст включает проекты, рабочие группы, отклики, задачи, профили, компетенции, отчётность и связанную аналитику.

Service Desk является **отдельным бизнес-модулем платформы**.

Он не является:

- частью проекта;
- типом проектной задачи;
- расширением откликов;
- рабочим пространством проектного менеджера;
- функцией обычного сотрудника проектного модуля.

Service Desk должен существовать как самостоятельный bounded context.

## 1.1. Жёсткая граница с Projects

Service Desk **не должен иметь предметных связей** с:

- `projects`;
- `project_tasks`;
- `project_members`;
- `project_responses`;
- проектными компетенциями;
- проектными ролями.

Запрещено добавлять:

```text
project_id
project_task_id
```

в заявку Service Desk.

Запрещено:

- создавать заявку из проектной задачи;
- отображать заявки Service Desk в проекте;
- использовать `project_manager` как автоматического исполнителя или согласующего;
- использовать `employee` как автоматического заявителя.

Общее между модулями допускается только на платформенном уровне:

- identity пользователя;
- единый app shell;
- общая дизайн-система;
- shared frontend infrastructure;
- общие технические библиотеки;
- observability;
- общая инфраструктура деплоя, если это соответствует репозиторию.

---

# 2. Цель Service Desk

Реализовать полноценный модуль обработки внутренних сервисных заявок университета.

Service Desk должен обеспечивать:

- единый каталог услуг;
- иерархию категорий;
- услуги с динамическими шаблонами;
- создание заявки по конкретной услуге;
- черновики;
- отправку заявки;
- многоэтапное согласование;
- услуги без согласования;
- назначение исполнителя;
- рабочую очередь исполнителя;
- полный статусный жизненный цикл;
- ожидание уточнения от заявителя;
- ожидание внешнего действия;
- выполнение;
- закрытие;
- отмену;
- приоритеты;
- комментарии;
- внутренние комментарии;
- вложения;
- историю изменений;
- уведомления внутри платформы;
- подготовленную архитектуру email-уведомлений;
- SLA;
- рабочие календари SLA;
- эскалации;
- дашборды;
- бизнес-метрики;
- технические метрики;
- управление каталогом;
- управление шаблонами;
- версионирование шаблонов;
- управление согласованиями;
- управление маршрутизацией;
- управление доступом менеджеров;
- администрирование Service Desk.

Главная продуктовая цепочка:

```text
менеджер выбирает услугу
        ↓
заполняет форму по шаблону
        ↓
сохраняет черновик или отправляет заявку
        ↓
заявка получает номер
        ↓
при необходимости проходит согласование
        ↓
назначается исполнитель
        ↓
исполнитель работает с заявкой
        ↓
при необходимости запрашивает уточнение
        ↓
фиксирует решение
        ↓
заявка закрывается
        ↓
вся история, SLA и метрики сохраняются
```

---

# 3. Архитектурная граница модуля

## 3.1. Не перестраивать весь `prom` в новую монорепу

Текущие директории:

```text
backend/
frontend/
```

сохраняются.

Не переносить текущий Projects backend в:

```text
services/projects/
```

Не переносить frontend в:

```text
apps/web/
```

Не создавать `packages/shared-ui`, `packages/shared-auth` и другие workspace packages только потому, что такая схема выглядит архитектурно красиво.

Любой подобный крупный refactor требует отдельной причины и не должен быть побочным эффектом внедрения Service Desk.

## 3.2. Service Desk — отдельный sibling backend service

Создать рядом с текущим backend отдельный backend Service Desk.

Рекомендуемое имя директории:

```text
service-desk-backend/
```

Итоговая структура верхнего уровня:

```text
prom/
  backend/                 # существующий Projects backend
  service-desk-backend/    # новый Service Desk backend
  frontend/                # единый frontend PROM
  SERVICE_DESK_SCREENSHOTS/
  docker-compose.yml
  dev.cmd
  dev.sh
  .github/
```

Не вкладывать Service Desk в:

```text
backend/app/modules/service_desk
```

Причина:

- Projects и Service Desk являются разными bounded contexts;
- текущий backend глубоко связан с Projects `UserRole`, `User` и project routes;
- последующие модули платформы не должны превращать один backend в бесконечный набор несвязанных доменов.

## 3.3. Внутренняя архитектура `service-desk-backend`

Новый backend должен сохранить знакомый команде принцип:

```text
api
core
modules
```

То есть новый сервис архитектурно похож на текущий backend, но владеет только Service Desk domain.

## 3.4. Отдельное владение данными

Service Desk должен использовать отдельную PostgreSQL database.

В `docker-compose.yml` добавить отдельный DB service, например:

```text
service_desk_db
```

Development mapping может использовать отдельный host port, например `5433`, чтобы не конфликтовать с существующим `db:5432`.

Создать отдельный volume:

```text
service_desk_pg_data
```

Не использовать таблицы текущего `project_showcase` как database Service Desk.

Недопустимо:

- прямые FK Service Desk в `backend` tables;
- прямые FK на текущую таблицу `users`;
- импорт SQLAlchemy models Projects;
- импорт repositories Projects;
- общая SQLAlchemy session между двумя backend services.

## 3.5. Frontend остаётся единым

Не создавать отдельный React-проект для Service Desk.

Service Desk добавляется в текущий:

```text
frontend/
```

Используются:

- существующий `BrowserRouter`;
- существующий app shell;
- текущий `Header`;
- текущая FSD-структура;
- `shared/ui`;
- текущие CSS variables и визуальные паттерны `globals.css`.

Service Desk должен ощущаться как новый модуль той же платформы.

## 3.6. Два API base URL

Текущий Projects frontend использует:

```text
VITE_API_BASE_URL
```

Его не переименовывать и не ломать без необходимости.

Добавить:

```text
VITE_SERVICE_DESK_API_BASE_URL
```

Например локально:

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_SERVICE_DESK_API_BASE_URL=http://localhost:8001/api/service-desk
```

Создать отдельный:

```text
serviceDeskApiClient
```

или общий configurable client factory.

Не переписывать все существующие Projects API вызовы ради Service Desk.

## 3.7. Token storage должен быть общим

Текущий token storage находится внутри `shared/api/client.ts`.

Для двух API clients рекомендуется небольшой platform-level refactor:

```text
frontend/src/shared/auth/tokenStorage.ts
```

Пример обязанностей:

```text
getToken()
setToken()
clearToken()
```

Текущий Projects `apiClient` и новый `serviceDeskApiClient` используют один token storage.

Это небольшой shared refactor.

Не создавать второй localStorage token Service Desk.

## 3.8. Development startup

Обновить:

```text
dev.cmd
dev.sh
```

Они должны уметь:

1. поднять существующий Projects PostgreSQL;
2. поднять Service Desk PostgreSQL;
3. применить Projects migrations;
4. применить Service Desk migrations;
5. запустить Projects backend;
6. запустить Service Desk backend;
7. запустить единый frontend.

После запуска development environment:

```text
Frontend:             http://localhost:5173
Projects Swagger:     http://localhost:8000/docs
Service Desk Swagger: http://localhost:8001/docs
```

Порты допускается адаптировать, если они уже заняты или repo convention требует другое.

---

# 4. Identity, аутентификация и авторизация

## 4.1. Identity пользователя общая для платформы

У пользователя не должно быть отдельного аккаунта Projects и отдельного аккаунта Service Desk.

Платформенная identity едина.

У Service Desk пользователь идентифицируется стабильным:

```text
identity_user_id / subject / sub
```

Дополнительно Service Desk может хранить локальный профиль:

- email;
- display name;
- department;
- position.

Эти данные не должны быть FK на `projects.users`.

## 4.2. Service Desk не использует проектные роли

Следующие роли не определяют доступ к Service Desk:

```text
employee
project_manager
projects_admin
```

Пользователь не получает доступ к Service Desk только потому, что он зарегистрирован в `prom`.

Пользователь не получает право создавать заявку только потому, что он `employee`.

## 4.3. Модель доступа Service Desk

Предметно в Service Desk существуют:

```text
manager
service_desk_admin
platform_admin
```

### manager

Уполномоченный менеджер университета.

Менеджер может быть в разных заявках:

- заявителем;
- исполнителем;
- согласующим.

Это **не три разные роли пользователя**.

Пример:

```text
Пользователь А
тип доступа: manager

SD-2026-001:
requester

SD-2026-002:
assignee

SD-2026-003:
approver
```

### service_desk_admin

Администратор только Service Desk.

Имеет полный административный доступ к Service Desk:

- заявки;
- каталог;
- шаблоны;
- версии;
- согласования;
- назначения;
- SLA;
- календари;
- права Service Desk;
- дашборды;
- отчётность.

Не получает автоматически права администратора Projects.

### platform_admin

Администратор всей платформы.

Имеет полный доступ ко всем модулям платформы.

Предлагаемая общая модель администраторов платформы:

```text
platform_admin
projects_admin
service_desk_admin
future_module_admin
```

Не использовать название `prom_admin`, так как оно не объясняет предметную область.

## 4.4. Контекстные роли заявки

Следующие понятия являются отношением пользователя к конкретной заявке:

```text
requester
assignee
approver
```

Не создавать глобальные enum-роли:

```text
sd_requester
sd_technician
sd_approver
sd_coordinator
```

если для этого нет отдельного подтверждённого бизнес-требования.

## 4.5. Capabilities менеджера

Для ограничения полномочий менеджеров Service Desk должна поддерживаться capability-модель.

Минимальные capabilities:

```text
service_desk.access
service_desk.create_request
service_desk.be_assignee
service_desk.approve
service_desk.assign
service_desk.change_priority
service_desk.view_all_tickets
service_desk.view_reports
service_desk.manage_catalog
service_desk.manage_templates
service_desk.manage_approval_workflows
service_desk.manage_routing
service_desk.manage_sla
service_desk.manage_access
```

`service_desk_admin` получает все Service Desk capabilities.

`platform_admin` имеет platform-wide bypass.

Для менеджера capability назначаются административно.

Таким образом можно поддержать ситуацию:

```text
Менеджер 1:
- создаёт заявки
- согласует

Менеджер 2:
- исполнитель
- не создаёт заявки

Менеджер 3:
- создаёт заявки
- может быть исполнителем

Главный менеджер:
- создаёт
- согласует
- назначает
- видит отчёты
```

без создания десятков ролей.

## 4.6. Текущий PROM JWT и будущая аутентификация ТюмГУ

Фактически текущий `prom` создаёт JWT со следующими claims:

```text
sub
exp
```

`sub` содержит строковое UUID текущего пользователя.

Текущий JWT **не содержит**:

```text
email
display_name
role claims для Service Desk
capabilities
```

Поэтому Service Desk не должен ожидать эти данные в текущем token.

### Текущий development bridge

До появления корпоративного SSO ТюмГУ новый Service Desk backend может проверять JWT, выпущенный текущим `prom`, используя совместимую JWT-конфигурацию.

Из JWT Service Desk использует только:

```text
sub
```

`sub` становится:

```text
identity_user_id
```

в локальной `ServiceDeskUser`.

Service Desk по `identity_user_id` ищет собственную локальную запись и собственные capabilities.

Пример:

```text
JWT sub = 5d...uuid
        ↓
service_desk_users.identity_user_id
        ↓
Service Desk access_type + capabilities
```

Service Desk **не должен** после decode JWT делать запрос к таблице `backend.users`.

Service Desk **не должен** использовать Projects `UserRole` для принятия решения о доступе.

### Локальные profile fields Service Desk

Email, display name, department и position на текущем этапе читаются из локальной `ServiceDeskUser`.

Они могут быть созданы:

- seed data для development;
- Service Desk admin flow предоставления доступа.

После появления корпоративной identity интеграции источник этих полей может измениться.

### Важное ограничение текущего bridge

Текущий login flow всё ещё живёт в существующем Projects backend.

Это временное ограничение текущей платформы, а не финальная целевая identity architecture.

Не выдавать его за интеграцию с ресурсами ТюмГУ.

### Корпоративная аутентификация ТюмГУ

Финальная аутентификация зависит от ЦИТ.

Не создавать:

- fake SSO;
- fake LDAP;
- фиктивный OAuth/OIDC provider;
- отдельную фейковую форму «корпоративного входа».

До получения документации интеграция имеет статус:

```text
BLOCKED_EXTERNAL
```

В `SERVICE_DESK_EXTERNAL_DEPENDENCIES.md` зафиксировать:

```text
Корпоративная аутентификация ТюмГУ
Статус: BLOCKED_EXTERNAL

Необходимы:
- протокол;
- issuer / authority;
- client id;
- scopes;
- claims;
- user subject semantics;
- logout flow;
- refresh/session policy;
- MFA requirements;
- mapping университетских пользователей.
```

Архитектура Service Desk должна позволять заменить current PROM JWT verifier на corporate identity verifier без переписывания Service Desk domain logic.

---

# 5. Пользовательские сущности Service Desk

## 5.1. ServiceDeskUser

Локальная Service Desk-проекция платформенного пользователя.

Поля:

```text
id: UUID
identity_user_id: str/UUID
email: str
display_name: str
department: str | None
position: str | None
access_type: manager | service_desk_admin
is_active: bool
created_at
updated_at
```

Ограничения:

- `identity_user_id` unique;
- email не использовать как стабильный primary identity;
- деактивированный пользователь не может выполнять новые действия;
- исторические заявки пользователя сохраняются.

## 5.2. ServiceDeskUserCapability

Поля:

```text
id
service_desk_user_id
capability
scope_type nullable
scope_id nullable
created_at
created_by
```

`scope_type/scope_id` позволяют в будущем ограничивать capability:

- категорией;
- услугой;
- группой услуг.

Если текущие материалы не дают точной scope-модели, реализовать базовую глобальную capability-модель, но структуру не блокировать для scoped permissions.

---

# 6. Каталог услуг

## 6.1. Категории

Каталог иерархический.

`ServiceDeskCategory`:

```text
id: UUID
title: str
description: str | None
parent_id: UUID | None
position: int
is_active: bool
created_at
updated_at
deleted_at nullable
```

Поддержать:

- корневые категории;
- дочерние категории;
- сортировку;
- скрытие неактивных;
- soft delete;
- восстановление;
- одинаковые названия в разных ветках, если это требуется структурой.

Не делать `title` глобально unique.

## 6.2. Услуги

`ServiceDeskService`:

```text
id: UUID
category_id: UUID
title: str
short_description: str | None
description: str | None
is_active: bool
position: int
created_at
updated_at
deleted_at nullable
```

Уникальность:

```text
category_id + title
```

допустима, если подтверждена текущими данными.

Одинаковое название услуги в разных категориях должно поддерживаться.

## 6.3. Начальные категории

Создать:

- `Сопровождение учебного процесса`
- `Административно-хозяйственное сопровождение`
- `ГИА: Администрирование`
- `ГИА: Работа с обучающимися`
- `Практика: Организация и договоры`
- `Практика: Сопровождение`

По разделу `Практика` не терять услуги.

Если референсные скриншоты показывают общую категорию `Практика`, сохранить возможность собрать такую структуру административно.

## 6.4. Сопровождение учебного процесса

Услуги:

- Перенос занятий, замена преподавателя.
- Обеспечение подписания индивидуальных планов преподавателей.
- Ознакомление ППС с приказами.
- Составление графика консультаций.
- Составление перечня дисциплин и списка ППС школы.
- Бронирование аудиторий.
- Трудоустройство выпускников.

Форма переноса занятий: использовать `SERVICE_DESK_SCREENSHOTS/image1.png` как функциональный референс.

## 6.5. Административно-хозяйственное сопровождение

Услуги:

- Бронирование аудиторий.
- На печать в Издательство.
- Роль табельщика: табель рабочего времени, график отпусков.
- Ввоз/вывоз и внос/вынос материальных ценностей.
- Допуск в здание.
- Оформление и регистрация исходящего документа.
- Транспортное обслуживание.
- Получение со склада, кроме компьютерной техники.
- Заказ сувенирной продукции.
- График отпусков.

Референсы:

```text
image2.png  — бронирование аудитории
image7.png  — материальные ценности
image8.png  — допуск в здание
image52.png — справочник/выбор адреса, если соответствует экрану
```

## 6.6. ГИА: Администрирование

Услуги:

- Заказ воды.
- Установка камер.
- Запуск проекта приказа о составе ГЭК.
- Запуск договора с председателем/членом ГЭК.
- Подготовка обоснования цены договора.
- Создание представления на допуск в здание членов ГЭК.
- Создание ЭСЗ на допуск в здание членов ГЭК.
- Запуск проекта приказа о внесении изменений в приказ о составе ГЭК.
- Подготовка списка председателей ГЭК на следующий календарный год.
- Подготовка приказа об организации и проведении ГИА по ОП ВО.
- Подготовка приказа о распределении студентов по группам для проведения ГИА.
- Подготовка приказа о предоставлении ВКР в ГЭК.
- Подготовка приказа о подготовке и оформлении билетов к заседанию ГЭК.
- Подготовка приказа о подготовке отчёта «Итоги ГИА».
- Подготовка приказа о передаче ВКР в библиотеку.
- Подготовка приказа о передаче ВКР на архивное хранение.
- Рассылка информационных материалов студентам.
- Организация встречи со студентами.
- Подготовка материалов.
- Подготовка доп. соглашения о расторжении договора.
- Подготовка доп. соглашения на увеличение/уменьшение.
- Создание представления об изменении контингента.
- Внесение изменений в обоснование цены договора.
- Создание акта приёма-передачи оказанных услуг.

## 6.7. Практика

Услуги:

- Сопровождение практики.
- Подготовка приказа о направлении на практику.
- Заключение договора о практической подготовке.
- Подготовка ИУП/ИКУГ.
- Внесение изменений в приказ.
- Изменение сроков прохождения практики.
- Подготовка представления на практику.
- Подготовка отчёта руководителя практик.
- Размещение отчётов на файловых ресурсах.
- Организация встречи со студентами.
- Подготовка материалов.

`SERVICE_DESK_SCREENSHOTS/image45.png` использовать как функциональный референс формы по практике.

---

# 7. Динамические шаблоны услуг

## 7.1. Требование

Форма заявки не кодируется вручную под каждую услугу.

Администратор Service Desk должен иметь возможность создать услугу и собрать форму из полей.

Frontend рендерит форму по опубликованной версии шаблона.

Backend валидирует данные по той же версии шаблона.

## 7.2. Базовые системные поля заявки

На референсных формах виден общий паттерн:

- тема;
- описание;
- детальная информация;
- обязательные поля со звёздочкой;
- значения из справочников;
- даты;
- вложения.

Для всех заявок предусмотреть системные поля:

```text
title / subject
description
attachments
```

Администратор может управлять:

- default title;
- разрешением редактировать title;
- обязательностью description;
- help text.

## 7.3. Типы динамических полей

Обязательно поддержать:

```text
text
textarea
rich_text
select
multiselect
date
datetime
email
number
checkbox
file
user
```

Не удалять `rich_text`, `multiselect` и `user` из backend только потому, что первые seed-шаблоны используют их редко.

## 7.4. Template field

```text
id: UUID
template_version_id: UUID
key: str
label: str
field_type: enum
is_required: bool
position: int
help_text: str | None
placeholder: str | None
options: JSON | None
validation: JSON | None
visibility_rules: JSON | None
required_rules: JSON | None
created_at
updated_at
```

Уникальность:

```text
template_version_id + key
```

`key` является машинным стабильным ключом внутри версии шаблона.

## 7.5. Формат options

Пример:

```json
[
  {
    "label": "Ленина, 38",
    "value": "lenina_38"
  },
  {
    "label": "Республики, 9",
    "value": "respubliki_9"
  }
]
```

Для option допускается:

```text
label
value
position
is_active
metadata
```

## 7.6. Validation

Поддержать декларативные правила:

```text
min_length
max_length
min
max
regex
email
min_date
max_date
allowed_extensions
max_file_size
max_files
```

Backend является источником истины.

Frontend повторяет validation для UX.

## 7.7. Условная видимость и обязательность

Пример:

```json
{
  "field": "requires_substitute_teacher",
  "operator": "equals",
  "value": "yes"
}
```

Поддержать операторы:

```text
equals
not_equals
in
not_in
is_empty
is_not_empty
```

Поля:

```text
visibility_rules
required_rules
```

Пример:

```text
requires_substitute_teacher = yes
        ↓
показать:
substitute_teacher_full_name
substitution_start_at
substitution_end_at

и сделать их обязательными
```

## 7.8. Справочники

Справочные значения не должны обязательно храниться inline в `options`.

Поддержать:

```text
static options
dictionary source
user source
```

Нужны административные справочники минимум для значений, которые повторяются между услугами.

Например:

- адреса корпусов;
- дисциплины;
- типы/виды значений, встречающиеся в реальных формах.

`image52.png` проверить как референс поведения выбора адреса.

---

# 8. Версионирование шаблонов

Версионирование обязательно.

## 8.1. Проблема

Существующая заявка должна продолжать отображаться по той форме, по которой была создана.

Изменение шаблона не должно менять историю старых заявок.

## 8.2. Модель

`ServiceDeskTemplateVersion`:

```text
id: UUID
service_id: UUID
version: int
status: draft | published | archived
created_by
published_by nullable
created_at
published_at nullable
archived_at nullable
```

Услуга имеет одну текущую published version.

## 8.3. Правила

- редактировать опубликованную версию нельзя;
- для изменений создаётся новая draft version;
- draft можно редактировать;
- при публикации новая версия становится active;
- предыдущая published version становится archived;
- archived version не удаляется;
- заявка сохраняет `template_version_id`;
- старая заявка всегда рендерится по своей версии.

## 8.4. Что входит в snapshot версии

Версия должна фиксировать:

- системные настройки формы;
- поля;
- порядок полей;
- options или references на versioned dictionary;
- validation;
- conditional rules;
- approval workflow binding;
- routing binding;
- SLA binding.

Нельзя допустить, чтобы изменение услуги задним числом изменило:

- согласующих старой заявки;
- SLA старой заявки;
- обязательные поля старой заявки.

---

# 9. Примеры обязательных форм

Seed должен содержать минимум 11 утверждённых шаблонов:

1. Заказ воды.
2. Установка камер.
3. Бронирование аудиторий.
4. На печать в издательство.
5. Роль табельщика.
6. Ввоз/вывоз и внос/вынос материальных ценностей.
7. Допуск в здание.
8. Транспортное обслуживание.
9. Регистрация исходящего документа.
10. График отпусков.
11. Получение со склада, кроме компьютерной техники.

Все остальные услуги также должны присутствовать в каталоге.

Если для услуги нет полного состава полей в доступных референсах:

- услуга всё равно создаётся;
- не выдумывать «финальную утверждённую форму»;
- пометить шаблон как `draft`;
- зафиксировать нехватку полей в `SERVICE_DESK_OPEN_QUESTIONS.md`.

## 9.1. Бронирование аудитории

Референс:

```text
SERVICE_DESK_SCREENSHOTS/image2.png
SERVICE_DESK_SCREENSHOTS/image52.png
```

Поля:

```text
address
type: select/dictionary
required: true
label: Адрес корпуса брони аудитории

event_start_at
type: datetime
required: true
label: Дата и время начала мероприятия

event_end_at
type: datetime
required: true
label: Дата и время окончания мероприятия

booking_goal
type: text/textarea
required: true
label: Цель брони аудитории

approved_with
type: text
required: false
label: ФИО (с кем согласовано)
```

Правило:

```text
event_end_at >= event_start_at
```

Вложения поддерживаются.

## 9.2. Перенос занятий, замена преподавателя

Референс:

```text
SERVICE_DESK_SCREENSHOTS/image1.png
```

Поля:

```text
teacher_full_name
text
required

transfer_reason
textarea
required

discipline
select/dictionary
required

academic_hours
select
required

transfer_start_date
date
required

transfer_end_date
date
required

requires_substitute_teacher
select yes/no
required

substitute_teacher_full_name
text
conditionally required

substitution_start_at
datetime
conditionally required

substitution_end_at
datetime
conditionally required
```

Правила:

```text
transfer_end_date >= transfer_start_date

if requires_substitute_teacher == yes:
    substitute_teacher_full_name required
    substitution_start_at required
    substitution_end_at required

substitution_end_at >= substitution_start_at
```

## 9.3. Ввоз/вывоз и внос/вынос материальных ценностей

Референс:

```text
SERVICE_DESK_SCREENSHOTS/image7.png
```

Поля:

```text
event_name
text
required

import_at
datetime
required

export_at
datetime
required

inventory_file
file
required

asset_type
text
required

package
text
required

vehicle_number_model
text
required
```

Правило:

```text
export_at >= import_at
```

Обязательный файл с перечнем МЦ валидируется backend.

## 9.4. Допуск в здание

Референс:

```text
SERVICE_DESK_SCREENSHOTS/image8.png
```

Поля:

```text
person_full_name
textarea/text
required

equipment
textarea
optional

address
text/select/dictionary
required

access_start_at
datetime
required

access_end_at
datetime
required
```

Правило:

```text
access_end_at >= access_start_at
```

## 9.5. Практика

Референс:

```text
SERVICE_DESK_SCREENSHOTS/image45.png
```

Агент обязан открыть изображение и зафиксировать состав показанной формы.

Не подменять поля формы произвольными.

---

# 10. Заявка Service Desk

`ServiceDeskTicket`:

```text
id: UUID
number: str
service_id: UUID
template_version_id: UUID

requester_user_id: UUID
assignee_user_id: UUID | None

title: str
description: str | None

status: ServiceDeskTicketStatus
priority: ServiceDeskPriority

field_values: JSON

submitted_at nullable
approval_started_at nullable
approved_at nullable
rejected_at nullable
assigned_at nullable
work_started_at nullable
resolved_at nullable
closed_at nullable
cancelled_at nullable

created_at
updated_at
deleted_at nullable

sla_snapshot: JSON / normalized snapshot fields
routing_snapshot: JSON nullable
```

## 10.1. Номер заявки

Формат:

```text
SD-2026-000001
```

Требования:

- человекочитаемый;
- уникальный;
- создаётся при первой отправке заявки;
- draft может существовать без публичного номера или иметь temporary id;
- генерация номера должна быть concurrency-safe.

Не вычислять следующий номер через небезопасный:

```text
SELECT MAX(number) + 1
```

без блокировки/sequence.

## 10.2. Приоритеты

Сохранить:

```text
low
medium
high
critical
```

UI:

```text
Низкий
Средний
Высокий
Критический
```

Приоритет должен участвовать в:

- фильтрации;
- сортировке;
- SLA selection;
- routing;
- статистике;
- эскалациях.

---

# 11. Полный жизненный цикл заявки

Статусы нельзя упрощать.

Сохранить:

```text
draft
submitted
pending_approval
approved
rejected
assigned
in_progress
waiting_requester
waiting_external
resolved
closed
cancelled
```

## 11.1. Значение статусов

### draft

Заявка создана, но не отправлена.

Можно:

- редактировать;
- прикладывать файлы;
- удалить/отменить черновик;
- отправить.

### submitted

Заявка отправлена и зарегистрирована.

Система определяет:

- требуется ли approval workflow;
- какой routing применяется;
- какой SLA применяется.

Это технически и предметно значимый этап регистрации заявки.

### pending_approval

Заявка находится в процессе согласования.

Может иметь несколько этапов согласования.

### approved

Все обязательные этапы согласования завершены успешно.

Далее заявка должна быть назначена.

### rejected

Заявка отклонена на этапе согласования.

Причина отклонения обязательна.

### assigned

Исполнитель назначен.

Работа ещё не начата.

### in_progress

Исполнитель взял заявку в работу.

### waiting_requester

Для продолжения требуется ответ или информация от заявителя.

SLA pause behavior определяется SLA policy.

### waiting_external

Работа ожидает внешнего действия, документа, согласования или внешнего события.

SLA pause behavior определяется SLA policy.

### resolved

Исполнитель зафиксировал решение.

Обязателен `resolution_summary`.

### closed

Заявка окончательно закрыта.

### cancelled

Заявка отменена в допустимой точке workflow.

Причина отмены обязательна.

## 11.2. Happy path с согласованием

```text
draft
  ↓ submit
submitted
  ↓ workflow requires approval
pending_approval
  ↓ all mandatory stages approved
approved
  ↓ assign
assigned
  ↓ start work
in_progress
  ↓ resolve
resolved
  ↓ close
closed
```

## 11.3. Happy path без согласования

```text
draft
  ↓ submit
submitted
  ↓ approval not required
approved
  ↓ routing/default/manual assignment
assigned
  ↓ start work
in_progress
  ↓ resolve
resolved
  ↓ close
closed
```

Статус `approved` сохраняется даже для услуги без согласования как зафиксированная стадия допуска заявки к исполнению.

## 11.4. Уточнение

```text
in_progress
  ↓ request clarification
waiting_requester
  ↓ requester replies / required data provided
in_progress
```

## 11.5. Внешнее ожидание

```text
in_progress
  ↓ wait external
waiting_external
  ↓ external dependency completed
in_progress
```

## 11.6. Отклонение

```text
pending_approval
  ↓ reject
rejected
```

Причина обязательна.

## 11.7. Отмена

Допустимые переходы в `cancelled` должны определяться policy.

По умолчанию:

- requester может отменить `draft`, `submitted`, `pending_approval`;
- `service_desk_admin` и `platform_admin` могут отменить незакрытую заявку;
- отмена `in_progress` требует причины;
- `resolved` и `closed` не отменяются обычным действием.

## 11.8. Transition service

Все переходы выполняются через единый domain service/state machine.

Запрещено:

```python
ticket.status = requested_status
```

напрямую из route/repository.

Нужен явный transition layer:

```text
can_transition(actor, ticket, action)
perform_transition(...)
write_history(...)
update_timestamps(...)
update_sla(...)
create_notifications(...)
```

## 11.9. Матрица переходов

Создать в проекте:

```text
SERVICE_DESK_STATUS_TRANSITIONS.md
```

Минимально описать:

| From | Action | To | Кто |
|---|---|---|---|
| draft | submit | submitted | requester |
| submitted | start approval | pending_approval | system |
| submitted | skip approval | approved | system |
| pending_approval | complete approval | approved | system |
| pending_approval | reject | rejected | approver |
| approved | assign | assigned | assign-capable manager/admin |
| assigned | start | in_progress | assignee |
| in_progress | request clarification | waiting_requester | assignee |
| waiting_requester | reply | in_progress | requester/system |
| in_progress | wait external | waiting_external | assignee |
| waiting_external | resume | in_progress | assignee |
| in_progress | resolve | resolved | assignee |
| resolved | close | closed | permitted actor |
| allowed states | cancel | cancelled | permitted actor |

Матрица должна быть покрыта backend tests.

---

# 12. Согласования

Согласование является полноценным workflow.

Одного:

```text
requires_approval: bool
default_approver_user_id
```

недостаточно.

## 12.1. Настройка на уровне версии услуги

Администратор Service Desk определяет:

```text
approval_mode:
  none
  workflow
```

Если `none`:

```text
submitted → approved
```

Если `workflow`:

```text
submitted → pending_approval
```

Таким образом `service_desk_admin` явно определяет, какие услуги требуют согласования, а какие нет.

Это настройка услуги/версии шаблона, а не ручная отметка каждой уже созданной заявки.

## 12.2. Approval workflow

`ServiceDeskApprovalWorkflow`:

```text
id
template_version_id
name
is_active
created_at
```

`ServiceDeskApprovalStage`:

```text
id
workflow_id
position
title
decision_rule: any | all
created_at
```

`ServiceDeskApprovalStageApprover`:

```text
id
stage_id
service_desk_user_id
created_at
```

## 12.3. ANY / ALL

`any`:

- достаточно одного approve;
- stage становится approved;
- остальные pending approvals становятся skipped/not_required_for_completion.

`all`:

- каждый обязательный approver должен approve.

При reject:

- текущий stage rejected;
- ticket становится `rejected`;
- последующие stages не запускаются.

## 12.4. Snapshot workflow в заявку

При submit:

- текущий approval workflow копируется в ticket approval entities;
- изменения workflow услуги не меняют текущую заявку.

`ServiceDeskTicketApprovalStage`:

```text
id
ticket_id
position
title
decision_rule
status: pending | approved | rejected | skipped
started_at nullable
completed_at nullable
```

`ServiceDeskTicketApproval`:

```text
id
ticket_approval_stage_id
approver_user_id
status: pending | approved | rejected | skipped
decision_comment nullable
decided_at nullable
created_at
```

## 12.5. Кто согласует

Согласующим является менеджер, включённый в approval stage конкретной заявки.

Это контекст заявки.

Глобальная роль `approver` не создаётся.

Для согласующего необходимо capability:

```text
service_desk.approve
```

## 12.6. Админская настройка

`service_desk_admin` должен иметь UI, где для версии шаблона можно:

- включить/выключить согласование;
- добавить stage;
- переименовать stage;
- менять порядок stages;
- выбрать ANY/ALL;
- добавить согласующих;
- удалить согласующих;
- увидеть итоговый workflow перед публикацией версии.

---

# 13. Назначение исполнителя и маршрутизация

## 13.1. Исполнитель

Исполнитель — менеджер, назначенный в конкретной заявке:

```text
ticket.assignee_user_id
```

У пользователя должна быть capability:

```text
service_desk.be_assignee
```

## 13.2. Кто может назначать

Назначить исполнителя может:

- manager с `service_desk.assign`;
- `service_desk_admin`;
- `platform_admin`.

Отдельная глобальная роль `sd_coordinator` не вводится.

## 13.3. Manual assignment

Поддержать ручное назначение из:

- карточки заявки;
- рабочей очереди;
- bulk actions, если таблица поддерживает массовые действия.

## 13.4. Default assignment

Услуга/версия шаблона может иметь:

```text
default_assignee_user_id
```

При успешном завершении approval:

```text
если default assignee есть и активен
→ assigned
```

## 13.5. Routing rules

Так как существующее ТЗ уже предусматривает автоматическое правило назначения, routing нельзя исключать.

`ServiceDeskRoutingRule`:

```text
id
name
priority
is_active
conditions JSON
action JSON
created_at
updated_at
```

Поддержать условия минимум:

```text
service
category
priority
field_value
```

Действия минимум:

```text
assign_user
set_priority
```

Пример:

```json
{
  "conditions": [
    {
      "field": "category_id",
      "operator": "equals",
      "value": "..."
    },
    {
      "field": "priority",
      "operator": "equals",
      "value": "critical"
    }
  ],
  "action": {
    "type": "assign_user",
    "user_id": "..."
  }
}
```

Правила выполняются по `priority`.

История должна фиксировать:

```text
assignment_source:
manual
default
routing_rule
```

---

# 14. SLA

SLA является обязательной частью архитектуры и функциональности.

Нельзя ограничиться полем `overdue`.

## 14.1. SLA policy

`ServiceDeskSlaPolicy`:

```text
id
name
description nullable
is_active
business_calendar_id

first_response_minutes
resolution_minutes

created_at
updated_at
deleted_at nullable
```

## 14.2. SLA binding

SLA выбирается по:

- версии услуги;
- приоритету;
- routing/SLA rules.

Поддержать SLA rules:

```text
service
category
priority
field_value
```

SLA, выбранный при submit, фиксируется для заявки.

Изменение policy не должно задним числом менять сроки существующей заявки.

## 14.3. Business calendar

`ServiceDeskBusinessCalendar`:

```text
id
name
timezone
is_active
created_at
updated_at
```

`ServiceDeskBusinessHours`:

```text
id
calendar_id
weekday
start_time
end_time
```

Поддержать несколько рабочих интервалов на день.

Пример:

```text
ПН–ПТ
09:00–13:00
14:00–18:00
```

`ServiceDeskCalendarException`:

```text
id
calendar_id
date
type: holiday | working_day | custom_hours
start_time nullable
end_time nullable
description nullable
```

Часовой пояс должен быть явным.

Для ТюмГУ не хардкодить локальное время без timezone-aware datetime.

## 14.4. First response

Нужно определить первое значимое действие исполнителя.

По умолчанию first response фиксируется при первом из событий:

- исполнитель начал работу;
- исполнитель добавил публичный комментарий;
- исполнитель запросил уточнение.

Не считать:

- автоматическую историю;
- назначение исполнителя;
- внутренний комментарий без взаимодействия с заявителем;

если это отдельно не настроено policy.

## 14.5. Resolution time

Resolution SLA заканчивается при:

```text
resolved
```

Closed time измеряется отдельно.

## 14.6. SLA pause

Policy должна определять статусы, приостанавливающие resolution timer.

Минимально конфигурируемые:

```text
waiting_requester
waiting_external
```

Не хардкодить оба как pause для всех policy.

На заявке хранить pause periods.

`ServiceDeskTicketSlaPause`:

```text
id
ticket_id
reason_status
started_at
ended_at nullable
duration_seconds nullable
```

## 14.7. SLA snapshot заявки

На ticket/SLA state хранить:

```text
sla_policy_id
sla_policy_snapshot

first_response_due_at
resolution_due_at

first_response_at nullable
resolved_at nullable

response_breached_at nullable
resolution_breached_at nullable

is_response_breached
is_resolution_breached

paused_seconds
```

## 14.8. SLA recalculation

При переходах:

```text
waiting_requester
waiting_external
in_progress
resolved
```

SLA engine должен корректно:

- начать pause;
- завершить pause;
- пересчитать resolution due date;
- зафиксировать breach.

## 14.9. SLA worker

Нужен background worker/process для:

- поиска приближающихся SLA deadlines;
- фиксации breach;
- запуска эскалаций;
- создания in-app notifications.

Не полагаться только на открытие страницы пользователем.

## 14.10. Эскалации

`ServiceDeskEscalationRule`:

```text
id
sla_policy_id
metric: first_response | resolution
threshold_percent
action_type
recipient_type
recipient_user_id nullable
is_active
```

Минимальные threshold examples:

```text
80%
100%
120%
```

Действия:

```text
create_in_app_notification
email_notification_when_available
```

Получатели:

```text
assignee
requester
service_desk_admin
specific_user
```

Email event формируется, но фактическая email delivery зависит от внешней интеграции.

---

# 15. Комментарии и коммуникация

## 15.1. Public comment

Видят:

- requester;
- assignee;
- approval participants, если имеют доступ к ticket;
- admins.

Используется для коммуникации по заявке.

## 15.2. Internal comment

Внутренняя заметка.

Видят:

- assignee;
- managers с доступом к ticket;
- service_desk_admin;
- platform_admin.

Requester не видит internal comments.

## 15.3. Model

`ServiceDeskTicketComment`:

```text
id
ticket_id
author_user_id
body
visibility: public | internal
created_at
updated_at nullable
deleted_at nullable
```

Изменение/удаление комментариев должно журналироваться.

## 15.4. Ответ заявителя при waiting_requester

Если ticket находится в `waiting_requester` и requester добавляет публичный комментарий или требуемое вложение:

- система фиксирует `requester_replied`;
- создаёт notification assignee;
- выполняет переход в `in_progress`, если policy этого действия настроена автоматически.

По умолчанию реализовать автоматический возврат:

```text
waiting_requester → in_progress
```

после публичного ответа requester.

---

# 16. Вложения

Вложения обязательны.

Поддержать:

- вложения заявки;
- вложения комментария;
- file-поля динамического шаблона.

## 16.1. Attachment ownership

Owner types:

```text
service_desk_ticket
service_desk_comment
service_desk_field_value
```

Если существующий attachment service находится внутри Projects domain, нельзя напрямую импортировать его domain model в Service Desk.

В таком случае:

- вынести storage abstraction в shared infrastructure package;
- или реализовать Service Desk attachment adapter на той же storage technology.

## 16.2. Файлы не хранить в PostgreSQL

Хранить metadata в БД.

Binary content — в storage.

Текущий local storage допускается для development, если он реально используется платформой.

Production storage integration с ресурсами ТюмГУ является внешней зависимостью, если ЦИТ не предоставил endpoint/доступ.

Не имитировать S3/корпоративное хранилище.

## 16.3. File validation

Поддержать:

- allowed extensions;
- MIME validation;
- max size;
- max file count;
- required file fields.

Backend validation обязательна.

## 16.4. Download permissions

Файл доступен только пользователю, который имеет доступ к ticket/comment/field value.

Не раздавать `storage/uploads` как полностью public static directory.

---

# 17. История изменений и audit trail

История обязательна.

`ServiceDeskTicketHistory`:

```text
id
ticket_id
actor_user_id nullable
event_type
from_value JSON nullable
to_value JSON nullable
metadata JSON nullable
created_at
```

События минимум:

```text
draft_created
submitted
status_changed
approval_started
approval_stage_started
approved
rejected
assigned
reassigned
priority_changed
field_updated
comment_added
internal_comment_added
attachment_added
attachment_removed
sla_assigned
sla_paused
sla_resumed
sla_warning
sla_breached
resolved
closed
cancelled
```

## 17.1. История неизменяема

Обычный пользователь не может:

- редактировать history;
- удалять history.

Администратор также не должен редактировать history через обычный UI.

## 17.2. Карточка заявки

Frontend показывает человеку понятную timeline:

```text
12:03 — Заявка создана
12:05 — Заявка отправлена
12:06 — Направлена на согласование
13:17 — Иван Иванов согласовал заявку
13:18 — Назначена Анне Петровой
14:01 — Заявка взята в работу
```

Не показывать пользователю raw JSON diff как основной UI.

Для admin/debug можно иметь details.

---

# 18. In-app уведомления

In-app notifications реализовать полностью.

## 18.1. Events

Создавать уведомления минимум для:

```text
ticket_submitted
approval_requested
approval_approved
approval_rejected
ticket_assigned
ticket_reassigned
ticket_started
clarification_requested
requester_replied
ticket_waiting_external
sla_warning
sla_breached
ticket_resolved
ticket_closed
ticket_cancelled
```

## 18.2. Notification model

`ServiceDeskNotification`:

```text
id
recipient_user_id
ticket_id nullable
event_type
title
body
is_read
created_at
read_at nullable
```

## 18.3. UI

В app shell `prom` добавить:

- notification indicator;
- unread count;
- список уведомлений;
- mark as read;
- mark all as read;
- переход к связанной заявке.

В Service Desk navigation показывать contextual counters:

- ждут моего согласования;
- назначены мне;
- ожидают моего ответа;
- SLA breaches, если пользователь имеет соответствующее право.

## 18.4. Email notifications

Email notification является обязательным целевым каналом Service Desk.

Но интеграция с почтовой инфраструктурой ТюмГУ сейчас зависит от внешних данных ЦИТ.

Поэтому:

- не мокать отправку;
- не писать fake SMTP success;
- не выводить «письмо отправлено», если оно реально не отправлено.

Архитектурно реализовать notification delivery abstraction:

```text
NotificationEvent
        ↓
NotificationDispatcher
        ↓
InAppChannel
EmailChannel
```

`InAppChannel` работает полностью.

`EmailChannel` имеет статус:

```text
BLOCKED_EXTERNAL
```

до получения реальной конфигурации.

События, которым требуется email, должны фиксироваться в delivery/outbox со статусом:

```text
blocked_external
```

а не `sent`.

## 18.5. External dependency

Создать запись в:

```text
SERVICE_DESK_EXTERNAL_DEPENDENCIES.md
```

с перечнем необходимых данных:

- SMTP/API;
- sender;
- authentication mechanism;
- allowed recipients;
- retry policy restrictions;
- rate limits;
- ЦИТ security requirements.

---

# 19. Notification outbox

Для надёжности использовать outbox.

`ServiceDeskNotificationOutbox`:

```text
id
event_id
channel
recipient
payload
status:
  pending
  processing
  sent
  failed
  blocked_external
retry_count
next_retry_at nullable
last_error nullable
created_at
processed_at nullable
```

In-app channel может доставляться worker-ом или транзакционно.

Email events сохраняются как `blocked_external`, пока channel unavailable.

Не терять событие.

---

# 20. Метрики и аналитика Service Desk

Service Desk должен иметь собственный административный дашборд.

## 20.1. Основные показатели

Показывать за выбранный период:

```text
Всего создано заявок
Закрыто заявок
Текущий backlog
Новые / submitted
На согласовании
Согласовано
Отклонено
Назначено
В работе
Ожидают заявителя
Ожидают внешнего действия
Выполнено / resolved
Закрыто
Отменено
```

## 20.2. Распределения

Показывать:

- по статусам;
- по приоритетам;
- по категориям;
- по услугам;
- по исполнителям.

## 20.3. Временные метрики

Считать:

```text
time_to_approval
time_to_assignment
first_response_time
resolution_time
close_after_resolution_time
```

Для каждой:

- average;
- median;
- P90.

Не ограничиваться average.

## 20.4. SLA metrics

Считать:

```text
response SLA compliance %
resolution SLA compliance %

response breaches
resolution breaches

active tickets near SLA breach
active breached tickets
```

## 20.5. Backlog aging

Buckets:

```text
0–1 день
2–3 дня
4–7 дней
8–14 дней
15+ дней
```

Считать по незакрытым заявкам.

## 20.6. Исполнители

Показывать:

```text
назначено заявок
в работе
waiting
resolved за период
closed за период
SLA breaches
median resolution time
```

Метрики не являются рейтингом эффективности сотрудника без дополнительного бизнес-решения.

Не добавлять «топ худших менеджеров».

## 20.7. Approval analytics

Показывать:

```text
pending approvals
average approval time
median approval time
P90 approval time
rejection rate
```

## 20.8. Reopen

В доступных требованиях нет однозначно подтверждённого полного сценария повторного открытия.

Не придумывать его молча.

Добавить вопрос в `SERVICE_DESK_OPEN_QUESTIONS.md`:

```text
Поддерживает ли целевой процесс reopen resolved/closed ticket?
Если да:
- кто может reopen;
- из какого статуса;
- возвращается ли SLA;
- увеличивается ли reopened_count?
```

До подтверждения не отображать фиктивное действие `Reopen`.

---

# 21. Технические метрики и observability

Service Desk должен отдавать технические метрики.

Если в платформе используется Prometheus, интегрировать с существующим подходом.

Минимально:

```text
service_desk_http_requests_total
service_desk_http_request_duration_seconds
service_desk_http_errors_total

service_desk_tickets_created_total
service_desk_ticket_transitions_total

service_desk_sla_breaches_total
service_desk_sla_worker_lag_seconds

service_desk_notification_outbox_size
service_desk_notification_failures_total

service_desk_db_pool_in_use
service_desk_db_pool_errors_total
```

Labels должны иметь ограниченную cardinality.

Не использовать `ticket_id`, `user_id`, `email` как Prometheus labels.

## 21.1. Health endpoints

Нужны:

```text
/health/live
/health/ready
/metrics
```

`ready` проверяет необходимые runtime dependencies.

Email integration, находящаяся в `BLOCKED_EXTERNAL`, не должна делать Service Desk permanently unready до её официального подключения.

---

# 22. Администрирование Service Desk

Service Desk admin UI должен быть полноценным.

Разделы:

```text
Обзор
Заявки
Каталог
Шаблоны
Согласования
Маршрутизация
SLA
Рабочие календари
Менеджеры и права
Уведомления / доставка
```

## 22.1. Каталог

Администратор может:

- создать категорию;
- создать подкатегорию;
- изменить;
- сменить порядок;
- деактивировать;
- восстановить;
- создать услугу;
- переместить услугу;
- изменить описание;
- деактивировать;
- восстановить.

## 22.2. Шаблоны

Администратор может:

- открыть service;
- увидеть версии;
- создать draft новой версии;
- копировать предыдущую published version;
- добавлять поля;
- редактировать поля;
- удалять поля draft;
- менять порядок drag-and-drop или explicit ordering controls;
- настраивать validation;
- настраивать conditions;
- preview формы;
- публиковать версию;
- архивировать старую версию.

## 22.3. Preview

Preview должен рендериться тем же dynamic form renderer, который используется при создании заявки.

Не делать отдельную «похожую» preview-форму.

## 22.4. Согласования

Администратор настраивает workflow версии услуги.

## 22.5. Маршрутизация

Администратор:

- создаёт rule;
- задаёт priority;
- включает/выключает;
- меняет порядок;
- preview результата rule evaluation, если возможно.

## 22.6. SLA

Администратор:

- создаёт policy;
- задаёт first response;
- задаёт resolution;
- выбирает business calendar;
- настраивает pause statuses;
- настраивает escalations;
- привязывает SLA к услугам/приоритетам.

## 22.7. Менеджеры и права

Администратор видит пользователей Service Desk.

Может:

- предоставить Service Desk access;
- убрать access;
- назначить manager/service_desk_admin;
- включить/выключить capabilities;
- деактивировать локальный SD access.

Изменение прав журналируется.

---

# 23. Frontend: визуальная и UX-концепция

## 23.1. Стиль PROM

Все страницы Service Desk должны выглядеть как часть существующего `prom`.

Агент обязан сначала проанализировать:

- Header;
- sidebar/navigation, если есть;
- PageLayout;
- Card;
- Table;
- Button;
- Input;
- Select;
- Textarea;
- Modal;
- Badge;
- Spinner;
- EmptyState;
- typography;
- spacing;
- border radius;
- responsive behavior.

Использовать существующие компоненты или расширять их.

Не создавать параллельный UI kit `ServiceDeskButton`, `ServiceDeskCard` без необходимости.

## 23.2. Скриншоты ManageEngine

Использовать для ответа на вопросы:

```text
какие поля есть?
какой смысл экрана?
какие действия доступны?
какая информация показана?
как устроена форма?
какие справочники используются?
```

Не использовать для ответа:

```text
какой цвет кнопки?
какой border radius?
как выглядит sidebar?
какой фон?
какой шрифт?
```

Визуальный ответ на эти вопросы берётся из `prom`.

---

# 24. Frontend architecture

Сохранить текущую Feature-Sliced Design структуру внутри существующего:

```text
frontend/src/
```

Фактический repo уже содержит:

```text
app/
pages/
widgets/
features/
entities/
shared/
```

Не создавать второй frontend.

Предлагаемые новые slices:

```text
frontend/src/
  app/
    routes/
      AppRouter.tsx

  pages/
    service-desk-catalog/
    service-desk-service/
    service-desk-my-tickets/
    service-desk-ticket-details/
    service-desk-workbench/
    service-desk-admin-dashboard/
    service-desk-admin-catalog/
    service-desk-admin-service/
    service-desk-admin-templates/
    service-desk-admin-approval/
    service-desk-admin-routing/
    service-desk-admin-sla/
    service-desk-admin-calendars/
    service-desk-admin-access/

  widgets/
    service-desk-catalog/
    service-desk-ticket-header/
    service-desk-ticket-timeline/
    service-desk-ticket-comments/
    service-desk-ticket-approvals/
    service-desk-workbench-table/
    service-desk-admin-nav/
    service-desk-notifications/

  features/
    create-service-desk-ticket/
    save-ticket-draft/
    submit-ticket/
    cancel-ticket/
    approve-ticket/
    reject-ticket/
    assign-ticket/
    transition-ticket-status/
    add-ticket-comment/
    add-internal-comment/
    upload-ticket-attachment/
    mark-notification-read/
    manage-service-template/
    publish-template-version/
    manage-approval-workflow/
    manage-routing-rule/
    manage-sla-policy/
    manage-service-desk-access/

  entities/
    service-desk-category/
    service-desk-service/
    service-desk-template/
    service-desk-ticket/
    service-desk-approval/
    service-desk-sla/
    service-desk-notification/
    service-desk-user/

  shared/
    api/
    auth/
    ui/
    config/
```

Названия новых slices должны соответствовать существующему kebab-case naming convention.

## 24.1. Маршрутизация

Service Desk routes добавить в существующий:

```text
frontend/src/app/routes/AppRouter.tsx
```

Не создавать второй BrowserRouter.

Не использовать существующие `AdminRoute` и `ManagerRoute` как Service Desk guards: они завязаны на Projects roles.

Добавить отдельные guards, например:

```text
ServiceDeskRoute
ServiceDeskAdminRoute
```

Их решение основывается на Service Desk `/me` и capabilities.

## 24.2. Auth provider

Текущий `AppProviders` содержит Projects-oriented flags:

```text
isAdmin
canManageProjects
```

Не добавлять туда десятки flags вида:

```text
isSdApprover
isSdTechnician
isSdRequester
...
```

Допустимые варианты:

1. отдельный `ServiceDeskAccessProvider`;
2. отдельный hook/query layer для Service Desk access;
3. расширение platform provider объектом capabilities.

Предпочтение:

```text
ServiceDeskAccessProvider
```

который загружает:

```text
GET Service Desk /me
```

только когда есть platform token и пользователь входит в Service Desk zone.

## 24.3. API client

Текущий:

```text
frontend/src/shared/api/client.ts
```

сохраняется для Projects.

Добавить:

```text
frontend/src/shared/api/serviceDeskClient.ts
```

или configurable API client factory.

Оба clients используют общий token storage.

## 24.4. Ошибки API

Текущий frontend уже нормализует FastAPI validation errors в `shared/api/client.ts`.

Не дублировать целиком этот код во втором client.

Вынести reusable error parsing/normalization в shared helper и использовать из обоих API clients.

Service Desk dynamic validation errors должны отображаться по русскому label поля шаблона, а не только по hardcoded `VALIDATION_FIELD_LABELS`.

## 24.5. Запрет на giant component

Не размещать всю Service Desk логику в:

```text
pages/ServiceDesk.tsx
```

Не делать giant page на тысячи строк.

Page собирает widgets/features/entities.

## 24.6. Не тащить новый frontend test stack без необходимости

В текущем frontend есть Vitest и Playwright, но нет обязательной React Testing Library component-test инфраструктуры.

Не добавлять jsdom + Testing Library только ради массового покрытия Service Desk UI.

Чистую бизнес-логику dynamic forms, conditions и action mapping выносить в testable pure functions и проверять Vitest.

Критический пользовательский UI flow проверять одним Playwright Service Desk smoke test.

---

# 25. Пользовательские страницы

## 25.1. `/service-desk`

Каталог услуг.

Доступ только при:

```text
service_desk.access
```

Показывать:

- поиск;
- категории;
- дочерние категории;
- услуги;
- краткие описания;
- быстрый переход к форме.

В стиле текущей витрины/карточек `prom`, если это соответствует UI.

## 25.2. `/service-desk/services/:serviceId`

Страница услуги и форма.

Показывать:

- название;
- описание;
- текущую published form;
- системные поля;
- dynamic fields;
- required marks;
- help text;
- attachments;
- validation errors.

Действия:

```text
Сохранить черновик
Отправить заявку
```

После submit:

- показать номер;
- перейти на ticket details;
- создать in-app notification о регистрации при необходимости.

## 25.3. `/service-desk/tickets`

Мои заявки.

Показывать только заявки, где current user requester.

Фильтры:

```text
status
service
category
priority
created period
search
```

Search:

- number;
- title;
- service title.

Pagination обязательна.

## 25.4. `/service-desk/tickets/:ticketId`

Карточка заявки.

Структура в стиле `prom`.

Показать:

### Header

- ticket number;
- title;
- status;
- priority;
- service;
- category.

### Summary

- requester;
- assignee;
- created;
- submitted;
- SLA due dates;
- SLA state.

### Request details

- description;
- dynamic fields;
- file fields;
- attachments.

### Approval

- stages;
- approvers;
- decisions;
- comments;
- current stage.

### Communication

- public comments;
- input;
- attachments.

### Internal notes

Только при наличии доступа.

### History

Человекочитаемая timeline.

### Available actions

Только действия, разрешённые transition/capability service.

Frontend не должен самостоятельно определять права только по UI role.

Backend должен возвращать:

```json
{
  "allowed_actions": [
    "approve",
    "reject",
    "assign"
  ]
}
```

или аналогичный policy result.

## 25.5. `/service-desk/workbench`

Рабочее место менеджера.

Фильтры:

```text
status
assignee
requester
priority
category
service
SLA state
overdue
created period
q
```

Quick views:

```text
На согласование
Назначены мне
В работе
Ожидают заявителя
Ожидают внешнего действия
Выполнены
Нарушение SLA
```

Таблица:

- number;
- title/service;
- requester;
- assignee;
- priority;
- status;
- SLA;
- created;
- updated.

Действия:

- approve;
- reject;
- assign;
- reassign;
- start;
- request clarification;
- wait external;
- resume;
- resolve;
- close;
- cancel;

только если они доступны.

---

# 26. Admin pages

## 26.1. `/admin/service-desk`

Dashboard.

Показывать метрики раздела 20.

## 26.2. `/admin/service-desk/tickets`

Все заявки.

Полные фильтры.

## 26.3. `/admin/service-desk/catalog`

Категории и услуги.

## 26.4. `/admin/service-desk/services/:serviceId`

Обзор услуги:

- metadata;
- versions;
- active version;
- SLA;
- approval;
- routing;
- usage stats.

## 26.5. `/admin/service-desk/templates/:versionId`

Template builder.

## 26.6. `/admin/service-desk/approvals`

Approval workflow administration.

## 26.7. `/admin/service-desk/routing`

Routing rules.

## 26.8. `/admin/service-desk/sla`

SLA policies and escalations.

## 26.9. `/admin/service-desk/calendars`

Business calendars.

## 26.10. `/admin/service-desk/access`

Service Desk managers and capabilities.

---

# 27. API

Base prefix рекомендуется:

```text
/api/service-desk
```

Фактический gateway prefix адаптировать под repo.

## 27.1. Current user / access

```text
GET /me
GET /me/capabilities
```

Service Desk `/me` возвращает Service Desk projection и capabilities.

## 27.2. Catalog

```text
GET /categories
GET /services
GET /services/{service_id}
GET /services/{service_id}/form
```

Filters:

```text
q
category_id
active
```

Для manager catalog возвращает только active/published services.

## 27.3. Drafts and tickets

```text
POST /tickets/drafts
PATCH /tickets/{ticket_id}
POST /tickets/{ticket_id}/submit

GET /me/tickets
GET /tickets/{ticket_id}

POST /tickets/{ticket_id}/cancel
```

Не объединять draft save и submit в один неявный endpoint.

## 27.4. Comments

```text
GET /tickets/{ticket_id}/comments
POST /tickets/{ticket_id}/comments
POST /tickets/{ticket_id}/internal-comments
```

## 27.5. Attachments

```text
POST /tickets/{ticket_id}/attachments
POST /comments/{comment_id}/attachments
POST /tickets/{ticket_id}/fields/{field_key}/attachments

GET /attachments/{attachment_id}/download
DELETE /attachments/{attachment_id}
```

DELETE permission зависит от состояния и ownership.

## 27.6. Approval

```text
GET /tickets/{ticket_id}/approvals
POST /tickets/{ticket_id}/approvals/{approval_id}/approve
POST /tickets/{ticket_id}/approvals/{approval_id}/reject
```

Reject request:

```json
{
  "comment": "Причина отклонения"
}
```

## 27.7. Assignment

```text
POST /tickets/{ticket_id}/assign
POST /tickets/{ticket_id}/reassign
```

## 27.8. Lifecycle actions

Предпочтительно explicit action endpoints:

```text
POST /tickets/{ticket_id}/start
POST /tickets/{ticket_id}/request-clarification
POST /tickets/{ticket_id}/wait-external
POST /tickets/{ticket_id}/resume
POST /tickets/{ticket_id}/resolve
POST /tickets/{ticket_id}/close
POST /tickets/{ticket_id}/cancel
```

Не делать универсальный:

```text
PATCH status = anything
```

как основной API.

Потому что action endpoints позволяют:

- валидировать payload;
- проверять actor;
- писать правильное событие;
- управлять SLA;
- создавать notification.

## 27.9. Resolve payload

```json
{
  "resolution_summary": "Работа выполнена...",
  "comment": "..."
}
```

`resolution_summary` required.

## 27.10. Workbench

```text
GET /workbench/tickets
GET /workbench/counters
```

## 27.11. Notifications

```text
GET /notifications
GET /notifications/unread-count
POST /notifications/{id}/read
POST /notifications/read-all
```

## 27.12. Admin catalog

```text
GET /admin/categories
POST /admin/categories
PATCH /admin/categories/{id}
POST /admin/categories/{id}/deactivate
POST /admin/categories/{id}/restore

GET /admin/services
POST /admin/services
PATCH /admin/services/{id}
POST /admin/services/{id}/deactivate
POST /admin/services/{id}/restore
```

## 27.13. Template versions

```text
GET /admin/services/{service_id}/versions
POST /admin/services/{service_id}/versions
GET /admin/template-versions/{version_id}
PATCH /admin/template-versions/{version_id}

POST /admin/template-versions/{version_id}/fields
PATCH /admin/template-fields/{field_id}
DELETE /admin/template-fields/{field_id}
POST /admin/template-versions/{version_id}/reorder-fields

GET /admin/template-versions/{version_id}/preview
POST /admin/template-versions/{version_id}/publish
```

## 27.14. Approval workflows

```text
GET /admin/template-versions/{version_id}/approval-workflow
PUT /admin/template-versions/{version_id}/approval-workflow

POST /admin/approval-workflows/{workflow_id}/stages
PATCH /admin/approval-stages/{stage_id}
DELETE /admin/approval-stages/{stage_id}
POST /admin/approval-workflows/{workflow_id}/reorder-stages

POST /admin/approval-stages/{stage_id}/approvers
DELETE /admin/approval-stage-approvers/{id}
```

## 27.15. Routing

```text
GET /admin/routing-rules
POST /admin/routing-rules
PATCH /admin/routing-rules/{id}
DELETE /admin/routing-rules/{id}
POST /admin/routing-rules/reorder
```

## 27.16. SLA

```text
GET /admin/sla/policies
POST /admin/sla/policies
PATCH /admin/sla/policies/{id}

GET /admin/sla/calendars
POST /admin/sla/calendars
PATCH /admin/sla/calendars/{id}

POST /admin/sla/policies/{id}/escalations
PATCH /admin/sla/escalations/{id}
DELETE /admin/sla/escalations/{id}
```

## 27.17. Access

```text
GET /admin/access/users
POST /admin/access/users
PATCH /admin/access/users/{id}
PUT /admin/access/users/{id}/capabilities
POST /admin/access/users/{id}/deactivate
POST /admin/access/users/{id}/activate
```

## 27.18. Stats

```text
GET /admin/stats/summary
GET /admin/stats/statuses
GET /admin/stats/services
GET /admin/stats/categories
GET /admin/stats/assignees
GET /admin/stats/sla
GET /admin/stats/backlog-aging
GET /admin/stats/approvals
```

Filters:

```text
date_from
date_to
category_id
service_id
assignee_user_id
priority
```

---

# 28. Backend architecture Service Desk

Создать отдельный Python project:

```text
service-desk-backend/
```

Стек должен соответствовать текущему backend:

- Python 3.14;
- FastAPI;
- Pydantic 2;
- SQLAlchemy 2;
- Alembic;
- PostgreSQL;
- PyJWT-compatible token verification;
- pytest для критического тестового контура.

Рекомендуемая структура:

```text
service-desk-backend/
  app/
    main.py

    api/
      router.py
      deps.py
      routes/
        catalog.py
        tickets.py
        comments.py
        attachments.py
        approvals.py
        workbench.py
        notifications.py
        admin_catalog.py
        admin_templates.py
        admin_approvals.py
        admin_routing.py
        admin_sla.py
        admin_access.py
        admin_stats.py

    core/
      config.py
      database.py
      security.py
      exceptions.py
      pagination.py
      observability.py

    modules/
      access/
      catalog/
      templates/
      tickets/
      approvals/
      routing/
      sla/
      comments/
      attachments/
      notifications/
      stats/
      audit/

  alembic/
  scripts/
    seed.py
  tests/
  pyproject.toml
```

Это намеренно похоже на существующий `backend/app/api`, `backend/app/core`, `backend/app/modules`.

Команде не нужно изучать совершенно другой backend style.

## 28.1. Не импортировать существующий backend как библиотеку

Запрещено делать runtime imports:

```python
from backend.app.modules.users.models import User
from backend.app.core.enums import UserRole
from backend.app.api.deps import CurrentUser
```

Service Desk — самостоятельный service.

Допускается перенести небольшую generic utility вручную или выделить реально общий код позже, но не создавать скрытую Python dependency Service Desk → Projects backend.

## 28.2. Router pattern

Как и текущий backend:

```text
main.py
↓
api_router
↓
routes
```

Service Desk routes подключаются внутри собственного FastAPI app.

Рекомендуемый внешний API prefix:

```text
/api/service-desk
```

Health endpoints могут находиться отдельно:

```text
/api/health
/health/live
/health/ready
/metrics
```

Выбрать один последовательный вариант и документировать.

## 28.3. Правило routes

Routes:

- parse HTTP;
- получают dependencies;
- вызывают service/use case;
- сериализуют response.

Routes не выполняют:

- status transitions;
- SLA calculation;
- approval calculation;
- routing;
- capability decision.

## 28.4. Domain services

Нужны логические сервисы:

```text
TicketLifecycleService
TicketAccessPolicy
ApprovalWorkflowService
RoutingService
SlaEngine
NotificationService
TemplateValidationService
TicketHistoryService
```

Названия можно адаптировать к текущему style.

Не дробить каждый тривиальный метод в отдельный use-case class ради формальной «clean architecture».

Цель — ясные business boundaries, а не максимальное количество файлов.

---

# 29. Транзакционность

Критические действия должны выполняться атомарно.

Пример submit:

```text
validate template
↓
persist field values
↓
assign ticket number
↓
snapshot template-related config
↓
select SLA
↓
calculate SLA
↓
create approval stages
↓
evaluate routing
↓
transition ticket
↓
write history
↓
write notification events
↓
COMMIT
```

Нельзя сохранить ticket как submitted, но потерять approval stages.

Пример approve:

```text
lock approval
↓
check pending
↓
write decision
↓
recalculate stage
↓
recalculate workflow
↓
transition ticket if complete
↓
write history
↓
create notification
↓
COMMIT
```

Защититься от double approve и concurrent transitions.

---

# 30. Миграции и индексы

Service Desk имеет **собственную Alembic history** внутри:

```text
service-desk-backend/alembic/
```

Не добавлять Service Desk tables в migrations текущего Projects `backend`.

Минимальные таблицы:

```text
service_desk_users
service_desk_user_capabilities

service_desk_categories
service_desk_services
service_desk_template_versions
service_desk_template_fields

service_desk_tickets

service_desk_approval_workflows
service_desk_approval_stages
service_desk_approval_stage_approvers

service_desk_ticket_approval_stages
service_desk_ticket_approvals

service_desk_routing_rules

service_desk_sla_policies
service_desk_business_calendars
service_desk_business_hours
service_desk_calendar_exceptions
service_desk_escalation_rules
service_desk_ticket_sla_pauses

service_desk_comments
service_desk_attachments

service_desk_ticket_history

service_desk_notifications
service_desk_notification_outbox
```

Индексы минимум:

```text
tickets.number unique
tickets.status
tickets.priority
tickets.requester_user_id
tickets.assignee_user_id
tickets.service_id
tickets.template_version_id
tickets.created_at
tickets.updated_at
tickets.deleted_at

ticket_approvals.approver_user_id
ticket_approvals.status

notifications.recipient_user_id + is_read

history.ticket_id + created_at

outbox.status + next_retry_at
```

Не создавать десятки speculative indexes заранее.

Добавить перечисленные индексы под подтверждённые workbench/statistics queries.

Для сложных workbench filters проверить generated SQL/query plan после появления реального запроса.

---

# 31. Валидация и бизнес-правила

Обязательные правила:

- нельзя создать draft по inactive service;
- нельзя submit без published template version;
- required fields валидируются backend;
- conditional required валидируются backend;
- field type валидируется backend;
- option value должен существовать;
- datetime timezone-aware;
- end >= start для связанных дат;
- required file field требует attachment;
- requester должен иметь create_request capability;
- assignee должен иметь be_assignee capability;
- approver должен иметь approve capability;
- assign actor должен иметь assign capability;
- inactive manager нельзя назначить;
- закрытую заявку нельзя редактировать;
- resolved ticket требует resolution summary;
- rejected approval требует comment;
- cancellation требует reason;
- все lifecycle transitions через state machine;
- все relevant actions пишутся в history;
- SLA snapshot неизменяем после создания, кроме runtime SLA state;
- template version старой заявки не меняется;
- requester не видит internal comments;
- download attachment проходит authorization;
- Service Desk manager не получает project permissions;
- Projects user не получает Service Desk access автоматически.

---

# 32. Seed / development data

Seed нужен для разработки и тестирования.

Это не мок внешней интеграции.

Создать Service Desk users:

```text
sd-admin@utmn.ru
access_type: service_desk_admin

sd-manager-1@utmn.ru
access_type: manager
capabilities:
- access
- create_request
- approve
- assign
- view_reports

sd-manager-2@utmn.ru
access_type: manager
capabilities:
- access
- be_assignee

sd-manager-3@utmn.ru
access_type: manager
capabilities:
- access
- create_request
- be_assignee
```

Если текущая auth platform требует существующего identity user, seed согласовать с текущей identity model.

Не использовать:

```text
employee@utmn.ru = requester
project_manager = technician
```

как предметное правило.

Создать tickets:

- draft;
- submitted;
- pending approval stage 1;
- pending approval stage 2;
- approved;
- assigned;
- in progress;
- waiting requester;
- waiting external;
- resolved;
- closed;
- cancelled;
- near SLA breach;
- breached SLA.

---

# 33. Минимальный обязательный тестовый контур

## 33.1. Цель

Тесты обязательны, но агент **не должен тратить токены и время на исчерпывающее покрытие каждого endpoint, каждого DTO и каждого варианта UI**.

В текущем `prom` уже есть:

- `pytest`;
- `vitest`;
- `Playwright`;
- GitHub Actions, запускающий полный текущий test/build/E2E pipeline на каждый push.

Поэтому стратегия:

> тестировать только бизнес-логику, поломка которой может нарушить жизненный цикл заявки, права, согласование, SLA или dynamic form; остальное проверять build, smoke и существующим CI.

Не ставить цель `100% coverage`.

Не генерировать тест «на каждый CRUD endpoint».

Не дублировать один и тот же сценарий в unit, integration, frontend unit и E2E без причины.

## 33.2. Backend: максимум полезности на небольшом числе тестов

Использовать parametrized/table-driven tests.

Минимальный набор test files:

```text
tests/test_lifecycle.py
tests/test_access.py
tests/test_approvals.py
tests/test_templates.py
tests/test_sla.py
tests/test_service_desk_smoke.py
```

Дополнительный test file создаётся только если появляется действительно отдельная критическая бизнес-логика.

### `test_lifecycle.py`

Один parametrized test проверяет матрицу разрешённых переходов.

Один parametrized test проверяет representative invalid transitions.

Не писать отдельную функцию:

```text
test_draft_to_submitted
test_submitted_to_pending
test_pending_to_approved
...
```

если они отличаются только входными значениями.

### `test_access.py`

Parametrized cases:

```text
no SD access → 403
manager + create_request → create allowed
manager without create_request → forbidden
requester sees own ticket
foreign manager without relation/capability → forbidden
assignee sees assigned ticket
approver sees pending approval
requester does not see internal comment
service_desk_admin sees all
```

### `test_approvals.py`

Проверить только:

1. approval not required;
2. ANY stage;
3. ALL stage;
4. multi-stage progression;
5. reject stops workflow.

Duplicate/concurrent decision проверить одним representative test, если locking/concurrency mechanism реализован.

### `test_templates.py`

Одним parametrized validation test покрыть representative field classes:

```text
required text
invalid select option
conditional required
date range
required file
```

Не писать отдельный backend test на каждый из:

```text
text
textarea
rich_text
email
number
checkbox
...
```

если они проходят через один и тот же generic validator.

Отдельно проверить:

```text
published version immutable
old ticket remains bound to old template version
```

### `test_sla.py`

Минимальные representative cases:

1. business hours + weekend;
2. calendar exception;
3. pause/resume;
4. breach + escalation event.

Не перебирать календарём все дни недели и все часы.

### `test_service_desk_smoke.py`

Один API-level happy path:

```text
draft
→ submit
→ approve
→ assign
→ start
→ request clarification
→ requester reply
→ resolve
→ close
```

Проверить по пути:

- status;
- history;
- in-app notification;
- SLA runtime state.

Это основной integration smoke.

## 33.3. Frontend Vitest: только pure business/UI logic

Текущий frontend использует Vitest без обязательной component testing stack.

Минимально создать:

```text
dynamicFormRules.test.ts
ticketActions.test.ts
```

### `dynamicFormRules.test.ts`

Parametrized cases:

- visibility rule;
- conditional required;
- option validation mapping;
- date pair client validation.

### `ticketActions.test.ts`

Проверить mapping:

```text
backend allowed_actions
→ доступные UI actions
```

и отсутствие запрещённых действий.

Не тестировать Button/Card/Badge.

Не делать snapshot tests страниц.

Не тестировать каждый Service Desk page через Vitest.

## 33.4. Playwright: один Service Desk E2E

Добавить:

```text
frontend/e2e/service-desk.spec.ts
```

Один основной сценарий:

1. SD admin/manager development identity входит существующим PROM login flow.
2. Открывает Service Desk.
3. Создаёт заявку по заранее seeded published service.
4. Отправляет.
5. Согласующий согласует.
6. Исполнитель назначается/назначается пользователем с правом.
7. Исполнитель берёт в работу.
8. Запрашивает уточнение.
9. Заявитель отвечает.
10. Исполнитель resolves.
11. Заявка closes.
12. Timeline содержит ключевые события.

Не создавать отдельный E2E для:

- каждого статуса;
- каждой услуги;
- каждого template field type;
- каждого admin CRUD screen.

## 33.5. Что запускать локально на каждую фичу

Перед feature commit запускать **только targeted checks**.

Если менялась backend business logic:

```bash
cd service-desk-backend
pytest tests/test_<related_area>.py -q
```

Если менялся frontend pure logic:

```bash
cd frontend
npm test -- <related-test-file>
```

Если менялся frontend TypeScript/UI:

```bash
cd frontend
npm run build
```

Playwright локально запускать:

- после завершения полного вертикального Service Desk flow;
- при изменении критического flow;
- перед финальным acceptance audit.

Не гонять полный Playwright после каждого поля или CSS-изменения.

## 33.6. Полный suite выполняет CI

После каждого push GitHub Actions должен запускать полный набор проверок.

Агент не обязан перед каждым commit локально выполнять:

```text
весь Projects pytest
весь Service Desk pytest
весь Vitest
полный Playwright
```

если targeted checks feature прошли.

Полный CI является regression gate.

Если CI упал:

- не игнорировать;
- не накапливать следующий Stage поверх красного CI;
- изучить только failed job/log;
- исправить;
- commit fix;
- push.

Не читать и не пересказывать агентом огромные green CI logs.

---

# 34. Нефункциональные требования

- Python 3.14.
- FastAPI.
- Pydantic 2.
- SQLAlchemy 2.
- Alembic.
- PostgreSQL.
- React latest stable.
- TypeScript.
- FSD.
- Русский UI.
- UTC в БД.
- timezone-aware datetime.
- Пагинация.
- Structured logging.
- Correlation/request id.
- Error normalization.
- Soft delete для сущностей, где требуется сохранение истории.
- Audit trail.
- Никаких файлов binary в PostgreSQL.
- Никаких публичных attachment URLs без access check.
- API docs должны генерироваться.
- Не ломать Projects.
- Не использовать Projects role model в Service Desk.
- Не добавлять Service Desk логику в Projects service.
- Не копировать визуальный стиль ManageEngine.

---

# 35. Внешние зависимости

Создать файл:

```text
SERVICE_DESK_EXTERNAL_DEPENDENCIES.md
```

На текущем этапе минимум:

## 35.1. ТюмГУ SSO / corporate identity

```text
status: BLOCKED_EXTERNAL
```

Необходимы данные ЦИТ.

До предоставления данных корпоративную интеграцию не реализовывать и не мокать.

## 35.2. Email delivery

```text
status: BLOCKED_EXTERNAL
```

Нужен реальный SMTP/API и требования ЦИТ.

In-app notifications реализуются полностью.

Email delivery architecture и outbox реализуются.

Фактическая отправка не считается выполненной до подключения реального канала.

## 35.3. Production file storage

Если ЦИТ требует внутреннее файловое хранилище:

```text
status: BLOCKED_EXTERNAL
```

до предоставления API/protocol/access.

Development storage не выдавать за production integration.

## 35.4. Backup policy / infrastructure

Если точный backup target и schedule определяет ЦИТ, зафиксировать внешнюю зависимость.

При этом Service Desk должен иметь documented backup requirements для своей DB и storage metadata.

---

# 36. Документация, которую агент должен создать

Кроме кода:

```text
README_SERVICE_DESK.md

SERVICE_DESK_ARCHITECTURE.md
SERVICE_DESK_STATUS_TRANSITIONS.md
SERVICE_DESK_PARITY_MATRIX.md
SERVICE_DESK_EXTERNAL_DEPENDENCIES.md
SERVICE_DESK_OPEN_QUESTIONS.md
SERVICE_DESK_DEMO_GUIDE.md
```

## 36.1. Parity matrix

Минимальный формат:

| Requirement | Screenshot | Backend | Frontend | Test | Status |
|---|---|---|---|---|---|
| dynamic service form | image1/image2/... | ... | ... | ... | ... |
| attachments | image1/image7/... | ... | ... | ... | ... |
| approval | related screenshots | ... | ... | ... | ... |
| assignment | related screenshots | ... | ... | ... | ... |
| status actions | related screenshots | ... | ... | ... | ... |

Агент должен дополнить matrix после просмотра **всей** папки screenshots.

---

# 37. Git workflow и порядок реализации

## 37.1. Главный принцип: одна законченная фича — commit — push

Агент не должен реализовать весь Service Desk локально и один раз запушить огромный diff в конце.

Работа должна постепенно нарастать в `origin/main`.

Правило:

```text
законченная feature slice
        ↓
targeted checks
        ↓
git diff review
        ↓
commit
        ↓
push origin main
        ↓
следующая feature
```

**Нельзя держать несколько законченных фич локально без push.**

Под «фичей» понимается законченная логическая возможность, а не отдельный файл.

Хорошая гранулярность:

```text
catalog categories and services
template versioning
dynamic form validation
ticket drafts and submit
ticket lifecycle state machine
approval workflow
assignment and routing
public/internal comments
attachments
SLA calendars
SLA runtime and breaches
in-app notifications
workbench
admin catalog UI
admin template builder
admin SLA UI
metrics dashboard
```

Плохая гранулярность:

```text
add model
add schema
add repository
add one button
fix import
```

Такие технические части одной фичи должны попадать в один feature commit.

## 37.2. Работа напрямую с `main`

По текущей задаче агент работает последовательно и пушит законченные feature commits в:

```text
origin/main
```

Перед началом:

```bash
git status
git branch --show-current
git pull --ff-only origin main
```

Рабочая директория должна быть понятной.

Если обнаружены чужие незакоммиченные изменения:

- не удалять;
- не делать `git reset --hard`;
- не перетирать;
- зафиксировать проблему и отделить свои изменения.

## 37.3. Перед каждым commit

Минимально:

```bash
git status
git diff --check
git diff
```

Проверить, что diff относится к одной feature slice.

Запустить targeted checks из раздела 33.5.

Затем:

```bash
git add <только файлы текущей фичи>
git commit -m "<message>"
git push origin main
```

Не использовать без необходимости:

```bash
git add .
```

если working tree содержит посторонние изменения.

## 37.4. Commit messages

Использовать понятные сообщения.

Рекомендуемый формат:

```text
feat(service-desk): add service catalog
feat(service-desk): add template versioning
feat(service-desk): add ticket lifecycle
feat(service-desk): add approval workflow
feat(service-desk): add SLA engine
feat(service-desk): add in-app notifications
feat(service-desk): add manager workbench

fix(service-desk): preserve SLA pause duration
fix(service-desk): block foreign ticket access

test(service-desk): add lifecycle smoke coverage
docs(service-desk): update parity matrix
```

Не использовать:

```text
update
fix
new
changes
готово
```

как единственный смысл commit message.

## 37.5. После push

Текущий repository CI уже запускается на push.

После feature push:

- сохранить SHA текущего commit;
- не нужно тратить контекст на чтение green logs;
- если CI failure обнаружен, изучить failed job;
- исправить failure отдельным `fix(service-desk)` commit;
- push fix.

Не использовать force push в `main`.

Не переписывать уже опубликованную историю.

## 37.6. CI checkpoints

Чтобы не тратить время/контекст на ожидание полного CI после каждой маленькой feature, обязательная проверка CI выполняется:

```text
после Stage 1
после Stage 3
после Stage 4
после Stage 7
после Stage 8
после Stage 10
перед финальным отчётом
```

Если checkpoint CI red:

> остановить переход к следующему Stage и исправить regression.

## 37.7. Расширение текущего CI

Текущий CI уже проверяет:

```text
backend
frontend
Projects browser E2E
```

На раннем этапе Service Desk добавить отдельный job:

```text
service-desk-backend
```

Он должен:

1. setup Python 3.14;
2. установить `service-desk-backend` dev dependencies;
3. применить его migrations к CI DB;
4. запустить его seed;
5. выполнить Service Desk pytest.

Существующие backend/frontend jobs не удалять.

После готовности вертикального Service Desk flow существующий E2E job расширить:

- запустить Projects backend;
- запустить Service Desk backend на отдельном порту;
- запустить frontend с обоими API URL;
- выполнить существующий `mvp.spec.ts`;
- выполнить новый `service-desk.spec.ts`.

Не создавать десятки GitHub Actions jobs по каждой Service Desk feature.

## 37.8. Порядок реализации

Порядок нужен для контроля и commit history, но не означает сокращение scope.

### Stage 0. Repository inspection

Уже подтверждённая база описана в разделе 0.4.

Агент дополнительно проверяет актуальный HEAD перед началом.

Commit не нужен, если код не менялся.

### Stage 1. Service boundary and CI

Фичи и отдельные pushes:

1. `service-desk-backend` skeleton + health.
2. отдельная Service Desk DB/config/migrations base.
3. Service Desk CI job.
4. frontend second API base/client + shared token storage.
5. development startup integration.

После каждой законченной feature — push.

CI checkpoint.

### Stage 2. Catalog and template engine

Отдельные feature commits:

1. categories/services catalog.
2. template versioning.
3. dynamic fields and dictionaries.
4. validation and conditional rules.
5. template preview.
6. seed catalog/forms from confirmed screenshots.

### Stage 3. Ticket core

Отдельные feature commits:

1. drafts.
2. submit + concurrency-safe number.
3. ticket details/list.
4. lifecycle state machine.
5. history timeline.

CI checkpoint.

### Stage 4. Approval engine

Отдельные feature commits:

1. approval workflow configuration.
2. approval workflow snapshot.
3. ANY/ALL evaluation.
4. multi-stage progression and reject.
5. approval UI/actions.

CI checkpoint.

### Stage 5. Assignment and routing

Отдельные feature commits:

1. manual assignment/reassignment.
2. default assignment.
3. routing rule evaluation.
4. routing admin UI.

### Stage 6. Comments and attachments

Отдельные feature commits:

1. public/internal comments.
2. ticket/comment attachments.
3. dynamic file field attachments.
4. protected download.

### Stage 7. SLA

Отдельные feature commits:

1. business calendars.
2. calendar exceptions.
3. SLA policy/binding snapshot.
4. SLA calculation.
5. pause/resume.
6. breach worker.
7. escalation rules.
8. SLA admin UI.

CI checkpoint.

### Stage 8. Notifications

Отдельные feature commits:

1. in-app notification domain/events.
2. unread/read/read-all API.
3. notification center/badge.
4. contextual Service Desk counters.
5. notification outbox.
6. email channel external-blocked state.

CI checkpoint.

### Stage 9. Workbench

Feature commits:

1. workbench query and filters.
2. quick views/counters.
3. table/actions.
4. SLA indicators.

### Stage 10. Admin and analytics

Feature commits:

1. Service Desk dashboard summary.
2. time/SLA/backlog metrics.
3. assignee/approval analytics.
4. admin navigation polish.
5. access/capability administration.

CI checkpoint.

### Stage 11. Observability

Feature commits:

1. health/live/ready.
2. Prometheus metrics.
3. structured logging/request correlation.

### Stage 12. Parity audit and final smoke

1. просмотреть всю `SERVICE_DESK_SCREENSHOTS`;
2. обновить parity matrix;
3. закрыть подтверждённые gaps;
4. запустить targeted critical tests;
5. запустить полный CI;
6. пройти Service Desk E2E smoke;
7. проверить существующий Projects E2E;
8. обновить documentation.

Документационные исправления можно объединить в один финальный docs commit.

После Stage 12 scope считается реализованным только при прохождении acceptance criteria.

---

# 38. Acceptance criteria

## Access

- Пользователь без Service Desk access не видит Service Desk navigation.
- Direct API access возвращает 403.
- Projects `employee` не становится Service Desk requester автоматически.
- Projects `project_manager` не становится assignee/approver автоматически.
- Service Desk manager может совмещать контекст requester/assignee/approver.
- Service Desk admin не получает Projects admin автоматически.
- Platform admin имеет полный platform access.

## Catalog

- Категории и услуги отображаются.
- Подкатегории поддерживаются.
- Одинаковые названия услуг в разных категориях поддерживаются.
- Неактивная услуга не доступна для новой заявки.

## Templates

- Dynamic form работает.
- Все типы fields поддерживаются.
- Required validation backend.
- Conditional visibility работает.
- Conditional required работает.
- File field работает.
- Template versioning работает.
- Published version не меняется.
- Old ticket отображается по old version.
- Admin preview использует production renderer.

## Tickets

- Draft создаётся.
- Draft сохраняется.
- Submit создаёт ticket number.
- Ticket получает template snapshot/config binding.
- Все статусы из ТЗ поддерживаются.
- Invalid transition запрещён.
- History пишется.

## Approvals

- Service может не требовать approval.
- Service может иметь approval workflow.
- Multi-stage работает.
- ANY работает.
- ALL работает.
- Reject требует reason.
- Workflow snapshot не меняется после изменения service template.

## Assignment

- Manual assignment работает.
- Default assignment работает.
- Routing работает.
- Inactive/non-assignee user не назначается.
- Reassignment пишется в history.

## Lifecycle

- assigned → in_progress.
- in_progress → waiting_requester.
- requester reply возвращает в work.
- in_progress → waiting_external.
- waiting_external → in_progress.
- resolve требует resolution summary.
- resolved → closed.
- cancellation checks rights/state.

## Comments

- Public comments видны requester.
- Internal comments requester не видит.
- Comment actions audited.

## Attachments

- Ticket attachments.
- Comment attachments.
- Dynamic file fields.
- Required file validation.
- Authorized download.
- Binary not stored in DB.

## SLA

- SLA policy назначается.
- Business calendar применяется.
- Holidays/exceptions применяются.
- First response due считается.
- Resolution due считается.
- waiting statuses pause according to policy.
- SLA resumes.
- Breach detected background.
- Escalation creates in-app notification.
- SLA metrics calculated.

## Notifications

- In-app notifications работают.
- Unread count работает.
- Read/read all работает.
- Ticket link работает.
- Email delivery не мокается.
- Email channel честно отображается как external blocked until integration.

## Admin

- Catalog management.
- Template version management.
- Approval workflow management.
- Routing management.
- SLA management.
- Calendar management.
- Service Desk access/capability management.
- Dashboard.

## Metrics

- Summary.
- Status distribution.
- Service/category.
- Assignee workload.
- Approval metrics.
- SLA metrics.
- Backlog aging.
- Average/median/P90 time metrics.
- Prometheus technical metrics.

## Regression

- Projects pages работают.
- Projects APIs работают.
- Project roles не изменились из-за Service Desk.
- Service Desk не делает запросы к Projects domain tables.

---

# 39. Финальное требование к агенту GPT-5.5

Не делай «похожий Service Desk».

Не делай «быстрый MVP Service Desk».

Не сокращай scope до CRUD заявок.

Нужно реализовать отдельный полноценный Service Desk bounded context внутри платформы `prom`.

При этом учитывай **фактический текущий repository layout**:

```text
backend/
service-desk-backend/
frontend/
```

Не перестраивай весь repository в `apps/services/packages` без отдельной причины.

Обязательно:

- изучить актуальный `main`;
- изучить всю `SERVICE_DESK_SCREENSHOTS`;
- использовать скриншоты как функциональные референсы;
- не копировать ManageEngine визуально;
- делать UI в текущем стиле `prom`;
- сохранить существующий FSD frontend;
- оставить Projects backend отдельным;
- создать отдельный Service Desk backend;
- создать отдельную Service Desk DB/Alembic history;
- не использовать Projects roles как Service Desk access;
- считать manager основным предметным пользователем;
- считать requester, assignee и approver контекстом заявки;
- отделить `service_desk_admin` от Projects admin;
- считать `platform_admin` общеплатформенным администратором;
- сохранить все статусы;
- реализовать multi-stage approval;
- реализовать SLA;
- реализовать in-app notifications;
- не мокать недоступные интеграции ТюмГУ;
- документировать `BLOCKED_EXTERNAL`;
- реализовать template versioning;
- реализовать immutable audit history;
- реализовать бизнес- и технические metrics;
- создать минимальный критический тестовый контур из раздела 33;
- не тратить время на 100% coverage и дублирующие тесты;
- сохранить существующие Projects tests/E2E;
- расширить текущий GitHub Actions CI;
- вести parity matrix.

## 39.1. Git discipline обязательна

**Каждая законченная feature slice должна быть закоммичена и запушена в `origin/main` до начала следующей законченной фичи.**

Не держать весь Service Desk локально до конца работы.

Последовательность:

```text
feature
→ targeted checks
→ diff review
→ commit
→ push origin main
→ next feature
```

Текущий CI запускается после push.

Не читать green logs без необходимости.

На CI checkpoints обязательно убедиться, что pipeline green.

При failure:

```text
stop stage progression
→ inspect failed job
→ fix
→ commit
→ push
```

Не force push.

Не переписывать опубликованные commits.

## 39.2. Перед финальным отчётом

Агент должен:

1. пройти acceptance criteria;
2. пройти Service Desk smoke;
3. пройти существующий Projects E2E;
4. проверить финальный GitHub Actions CI;
5. обновить parity matrix;
6. перечислить `BLOCKED_EXTERNAL` integrations;
7. перечислить open questions;
8. перечислить фактически созданные migrations;
9. перечислить новые routes/pages;
10. перечислить feature commits Service Desk с short SHA и message;
11. подтвердить, что working tree clean;
12. подтвердить, что изменения запушены в `origin/main`;
13. подтвердить, что Projects regression не сломан;
14. подтвердить, что Service Desk визуально использует стиль `prom`, а реальные ServiceDesk screenshots использованы только как функциональные референсы.
