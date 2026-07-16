# 03_API_CONTRACT.md — API-контракт

Base URL:

```txt
/api
```

Формат ответа: JSON.

Ошибки должны возвращаться в понятном формате:

```json
{
  "detail": "Описание ошибки"
}
```

## Авторизация MVP

Авторизация может быть упрощённой.

Минимально нужно предусмотреть API:

```txt
POST /api/auth/request-code
POST /api/auth/verify-code
GET /api/me
```

На MVP можно сделать dev-flow:
- пользователь вводит email;
- backend проверяет, что email заканчивается на `@utmn.ru`;
- `request-code` создаёт/логирует код или возвращает dev-сообщение;
- `verify-code` возвращает access token;
- token хранится на frontend;
- `GET /api/me` возвращает текущего пользователя.

Можно использовать JWT.

## Public / Employee API

### GET /api/projects

Получить список проектов для витрины.

Публичная витрина не должна возвращать:
- `draft`;
- `archived`;
- проекты с `archived_at != null`.

Query params:

```txt
search?: string
status?: ProjectStatus
project_type?: ProjectType
sort?: created_at_desc | created_at_asc | priority_desc | priority_asc
limit?: number
offset?: number
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Стратегический проект",
      "short_description": "Краткое описание",
      "goal": "Цель проекта",
      "project_type": "strategic",
      "priority": "high",
      "status": "active",
      "start_date": "2026-09-01",
      "end_date": null,
      "responsible": {
        "id": "uuid",
        "full_name": "Иван Иванов",
        "email": "ivan@utmn.ru"
      },
      "responses_count": 3,
      "created_at": "2026-07-01T12:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### GET /api/projects/{project_id}

Получить детальную страницу проекта.

Response:

```json
{
  "id": "uuid",
  "title": "Стратегический проект",
  "short_description": "Краткое описание",
  "description": "Полное описание",
  "goal": "Цель проекта",
  "expected_result": "Ожидаемый результат",
  "project_type": "strategic",
  "priority": "high",
  "status": "active",
  "start_date": "2026-09-01",
  "end_date": null,
  "responsible": {
    "id": "uuid",
    "full_name": "Иван Иванов",
    "email": "ivan@utmn.ru"
  },
  "contact_email": "project@utmn.ru",
  "members": [
    {
      "id": "uuid",
      "full_name": "Мария Петрова",
      "email": "maria@utmn.ru",
      "member_role": "working_group_member"
    }
  ],
  "required_competencies": "Коммуникации, аналитика, организация мероприятий",
  "planned_tasks": "Подготовить план, собрать рабочую группу",
  "responses_count": 3,
  "created_at": "2026-07-01T12:00:00Z",
  "updated_at": "2026-07-01T12:00:00Z"
}
```

Если поля `required_competencies` и `planned_tasks` не вынесены в отдельные колонки, можно хранить их как nullable text в `projects`. Если агент считает нужным, добавь эти поля в модель.

### POST /api/projects/{project_id}/responses

Создать отклик на проект.

Request:

```json
{
  "full_name": "Анна Смирнова",
  "email": "anna@utmn.ru",
  "comment": "Хочу участвовать, потому что интересна тема проекта.",
  "competencies": "SMM, аналитика, организация мероприятий"
}
```

Validation:
- `full_name` required;
- `email` required;
- email должен быть `@utmn.ru`;
- `comment` optional but желательно;
- `competencies` optional;
- нельзя откликнуться на archived/draft проект.

Response:

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "full_name": "Анна Смирнова",
  "email": "anna@utmn.ru",
  "comment": "Хочу участвовать, потому что интересна тема проекта.",
  "competencies": "SMM, аналитика, организация мероприятий",
  "status": "new",
  "created_at": "2026-07-01T12:00:00Z"
}
```

## Admin API

Admin API должен требовать роль `admin`.

Для MVP можно временно разрешить `project_manager` те же права, но лучше сделать dependency `require_admin_or_manager`.

### POST /api/admin/projects

Создать проект.

Request:

```json
{
  "title": "Новый стратегический проект",
  "short_description": "Краткое описание",
  "description": "Полное описание",
  "goal": "Цель",
  "expected_result": "Ожидаемый результат",
  "project_type": "strategic",
  "priority": "high",
  "status": "active",
  "start_date": null,
  "end_date": null,
  "responsible_user_id": null,
  "contact_email": "project@utmn.ru",
  "required_competencies": "Аналитика, коммуникации",
  "planned_tasks": "Собрать команду, описать план"
}
```

Response: created project.

### PATCH /api/admin/projects/{project_id}

Редактировать проект.

Request может содержать частичные поля.

Response: updated project.

### DELETE /api/admin/projects/{project_id}

Архивировать проект.

Важно:
- не удалять физически;
- выставить `status = archived`;
- выставить `archived_at = now()`.

Response:

```json
{
  "ok": true
}
```

### GET /api/admin/projects

Получить все проекты для админки.

В отличие от публичной витрины, админка может видеть draft и archived.

Query params:

```txt
search?: string
status?: ProjectStatus
project_type?: ProjectType
sort?: created_at_desc | created_at_asc | priority_desc | priority_asc
limit?: number
offset?: number
```

### GET /api/admin/projects/{project_id}/responses

Получить отклики по проекту.

Query params:

```txt
status?: ProjectResponseStatus
limit?: number
offset?: number
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "project_id": "uuid",
      "project_title": "Стратегический проект",
      "full_name": "Анна Смирнова",
      "email": "anna@utmn.ru",
      "comment": "Хочу участвовать",
      "competencies": "SMM, аналитика",
      "status": "new",
      "created_at": "2026-07-01T12:00:00Z",
      "processed_by": null,
      "processed_at": null
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### GET /api/admin/responses

Получить все отклики.

Query params:

```txt
project_id?: string
status?: ProjectResponseStatus
search?: string
limit?: number
offset?: number
```

### PATCH /api/admin/responses/{response_id}

Изменить статус отклика.

Request:

```json
{
  "status": "contacted"
}
```

Response: updated response.

При изменении статуса:
- обновить `updated_at`;
- если статус меняется с `new/viewed` на обработанный статус, можно заполнить `processed_by` и `processed_at`;
- точную логику сделать простой: при любом PATCH статуса заполнять `processed_by` текущим пользователем и `processed_at = now()`.

### GET /api/admin/stats

Базовая статистика.

Response:

```json
{
  "projects_total": 12,
  "projects_active": 7,
  "projects_archived": 2,
  "responses_total": 34,
  "responses_new": 6,
  "responses_accepted": 8,
  "responses_rejected": 3,
  "responses_by_project": [
    {
      "project_id": "uuid",
      "project_title": "Стратегический проект",
      "responses_count": 5
    }
  ]
}
```
