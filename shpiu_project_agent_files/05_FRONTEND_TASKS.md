# 05_FRONTEND_TASKS.md — задачи для frontend

## Цель

Реализовать frontend MVP на React latest stable + TypeScript по архитектуре Feature-Sliced Design.

## Рекомендуемая структура

```txt
frontend/
  src/
    app/
      providers/
        AppProviders.tsx
      routes/
        AppRouter.tsx
      styles/
        globals.css
      main.tsx

    pages/
      projects-list/
        ui/ProjectsListPage.tsx
      project-details/
        ui/ProjectDetailsPage.tsx
      admin-projects/
        ui/AdminProjectsPage.tsx
      admin-responses/
        ui/AdminResponsesPage.tsx
      admin-stats/
        ui/AdminStatsPage.tsx
      login/
        ui/LoginPage.tsx

    widgets/
      header/
        ui/Header.tsx
      project-card-list/
        ui/ProjectCardList.tsx
      admin-projects-table/
        ui/AdminProjectsTable.tsx
      admin-responses-table/
        ui/AdminResponsesTable.tsx
      project-details/
        ui/ProjectDetails.tsx

    features/
      auth-by-email/
        api/authApi.ts
        model/types.ts
        ui/LoginForm.tsx

      filter-projects/
        model/types.ts
        ui/ProjectFilters.tsx

      submit-project-response/
        api/submitProjectResponse.ts
        model/types.ts
        ui/ProjectResponseForm.tsx

      create-project/
        api/createProject.ts
        ui/CreateProjectForm.tsx

      edit-project/
        api/editProject.ts
        ui/EditProjectForm.tsx

      archive-project/
        api/archiveProject.ts
        ui/ArchiveProjectButton.tsx

      update-response-status/
        api/updateResponseStatus.ts
        ui/ResponseStatusSelect.tsx

    entities/
      project/
        api/projectApi.ts
        model/types.ts
        ui/ProjectCard.tsx
        ui/ProjectStatusBadge.tsx
        ui/ProjectPriorityBadge.tsx

      project-response/
        api/projectResponseApi.ts
        model/types.ts
        ui/ResponseStatusBadge.tsx

      user/
        api/userApi.ts
        model/types.ts

    shared/
      api/
        client.ts
      config/
        env.ts
      lib/
        date.ts
      ui/
        Button.tsx
        Input.tsx
        Textarea.tsx
        Select.tsx
        Modal.tsx
        Card.tsx
        Badge.tsx
        Table.tsx
        PageLayout.tsx
        EmptyState.tsx
        Spinner.tsx
```

## Роуты frontend

```txt
/
  -> редирект на /projects

/login
/projects
/projects/:projectId

/admin
/admin/projects
/admin/responses
/admin/stats
```

## Основные экраны

### 1. LoginPage

MVP-логика:
- поле email;
- кнопка «Войти»;
- проверка, что email заканчивается на `@utmn.ru`;
- вызвать `POST /api/auth/request-code`;
- затем можно автоматически вызвать `POST /api/auth/verify-code` с dev-code `000000` или показать поле кода;
- сохранить token;
- вызвать `GET /api/me`;
- перенаправить на `/projects`.

### 2. ProjectsListPage

Публичная витрина проектов.

Должна содержать:
- заголовок;
- поиск по названию;
- фильтр по статусу;
- фильтр по типу проекта;
- сортировка по дате создания / приоритету;
- список карточек проектов.

Карточка проекта должна содержать:
- название;
- краткое описание;
- цель;
- тип / уровень проекта;
- ответственный;
- статус;
- дата или период, если есть;
- количество откликов;
- кнопка «Подробнее»;
- кнопка «Откликнуться».

### 3. ProjectDetailsPage

Детальная страница проекта.

Показывать:
- полное описание;
- цель;
- ожидаемый результат;
- ответственного;
- рабочую группу;
- требуемые компетенции, если есть;
- предполагаемые задачи, если есть;
- сроки, если есть;
- статус;
- количество откликов;
- кнопку «Откликнуться».

Форма отклика:
- ФИО;
- email;
- комментарий;
- компетенции;
- кнопка отправки.

После отправки:
- показать success-состояние;
- очистить форму или закрыть modal;
- обновить количество откликов.

### 4. AdminProjectsPage

Админ-панель проектов.

Должна содержать:
- таблицу проектов;
- поиск;
- фильтр по статусу;
- фильтр по типу;
- кнопку «Создать проект»;
- действия:
  - редактировать;
  - архивировать.

Форма создания/редактирования проекта:
- title;
- short_description;
- description;
- goal;
- expected_result;
- project_type;
- priority;
- status;
- start_date;
- end_date;
- responsible_user_id или responsible email/name;
- contact_email;
- required_competencies;
- planned_tasks.

Даты optional.

### 5. AdminResponsesPage

Админ-панель откликов.

Должна содержать:
- список/таблицу откликов;
- фильтр по проекту;
- фильтр по статусу;
- поиск по ФИО/email;
- отображение:
  - проект;
  - ФИО;
  - email;
  - комментарий;
  - компетенции;
  - статус;
  - дата создания;
- возможность изменить статус.

Статусы:
- new;
- viewed;
- contacted;
- accepted;
- rejected;
- cancelled.

### 6. AdminStatsPage

Базовая статистика:
- всего проектов;
- активных проектов;
- архивных проектов;
- всего откликов;
- новых откликов;
- принятых;
- отклонённых;
- отклики по проектам.

Можно сделать карточками без графиков.

## API client

В `shared/api/client.ts` сделать общий клиент:

- base URL из env;
- автоматическое добавление Bearer token;
- обработка JSON;
- обработка ошибок.

Можно использовать `fetch`, axios не обязателен.

## UI

Сделать простой, чистый интерфейс.

Не тратить время на сложный дизайн. Главное:
- читаемые карточки;
- понятные таблицы;
- видимые статусы;
- нормальные empty/loading/error состояния.

## Types

Типы сущностей хранить в `entities/*/model/types.ts`.

Примеры:
- `Project`;
- `ProjectDetails`;
- `ProjectResponse`;
- `User`;
- enum/string union для статусов.

## MVP-ограничения

- Не делать drag-and-drop.
- Не делать сложные графики.
- Не делать уведомления.
- Не делать real-time.
- Не делать сложные права на уровне каждого проекта.
- Не делать полноценный профиль сотрудника.
- Не делать дизайн-систему на 100 компонентов.

## Acceptance criteria frontend

Frontend считается готовым, если:

- приложение стартует;
- можно войти через email `@utmn.ru`;
- список проектов загружается с backend;
- фильтры и поиск работают;
- страница проекта открывается;
- отклик отправляется;
- после отклика видно успешное состояние;
- админ может открыть список проектов;
- админ может создать проект;
- админ может редактировать проект;
- админ может архивировать проект;
- админ может открыть список откликов;
- админ может изменить статус отклика;
- базовая статистика отображается.
