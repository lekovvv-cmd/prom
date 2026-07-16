# 02_DOMAIN_MODEL.md — доменная модель и данные

## Enums

### UserRole

```txt
employee
project_manager
admin
```

### ProjectStatus

Предлагаемые статусы:

```txt
draft
active
paused
completed
archived
```

Расшифровка:
- `draft` — проект создан, но ещё не опубликован;
- `active` — проект активен и виден сотрудникам;
- `paused` — проект временно приостановлен;
- `completed` — проект завершён;
- `archived` — проект скрыт / архивирован.

### ProjectType

Пока в MVP использовать только:

```txt
strategic
```

Но enum и фильтр должны быть готовы к добавлению новых типов.

### ProjectPriority

```txt
low
medium
high
critical
```

Можно хранить как enum или строку.

### ProjectResponseStatus

```txt
new
viewed
contacted
accepted
rejected
cancelled
```

Расшифровка:
- `new` — новый отклик;
- `viewed` — просмотрен;
- `contacted` — с человеком связались;
- `accepted` — принят в рабочую группу;
- `rejected` — отклонён;
- `cancelled` — отозван / неактуален.

### ProjectMemberRole

```txt
manager
working_group_member
participant
```

## Таблицы

### users

```txt
id
email
full_name
role
department
position
created_at
updated_at
```

Поля:
- `id` — UUID или integer primary key;
- `email` — уникальный email;
- `full_name` — ФИО;
- `role` — employee / project_manager / admin;
- `department` — подразделение, nullable;
- `position` — должность, nullable;
- `created_at`;
- `updated_at`.

Ограничения:
- email должен быть уникальным;
- в MVP авторизация разрешена только для email на домене `@utmn.ru`.

### projects

```txt
id
title
short_description
description
goal
expected_result
project_type
priority
status
start_date nullable
end_date nullable
responsible_user_id nullable
contact_email nullable
created_by
created_at
updated_at
archived_at nullable
```

Поля:
- `title` — название проекта;
- `short_description` — краткое описание для карточки;
- `description` — полное описание;
- `goal` — цель проекта;
- `expected_result` — ожидаемый результат, nullable;
- `project_type` — на MVP `strategic`;
- `priority` — приоритет;
- `status` — статус;
- `start_date` — опционально;
- `end_date` — опционально;
- `responsible_user_id` — ответственный, nullable;
- `contact_email` — контактная почта, nullable;
- `created_by` — кто создал проект;
- `archived_at` — дата архивации, nullable.

Важно:
- даты должны быть nullable;
- архивирование лучше делать мягким удалением через `archived_at` и статус `archived`;
- публичная витрина не должна показывать архивные и draft-проекты.

### project_members

```txt
id
project_id
user_id
member_role
created_at
```

Назначение:
- хранить рабочую группу проекта;
- хранить руководителей, участников, членов рабочей группы.

### project_responses

```txt
id
project_id
user_id nullable
full_name
email
comment
competencies
status
created_at
updated_at
processed_by nullable
processed_at nullable
```

Поля:
- `project_id` — проект;
- `user_id` — пользователь, если найден / авторизован;
- `full_name` — ФИО откликнувшегося;
- `email` — email;
- `comment` — комментарий / мотивация;
- `competencies` — компетенции текстом;
- `status` — статус обработки;
- `processed_by` — кто обработал отклик;
- `processed_at` — когда обработал.

Важно:
- после создания отклика проект должен показывать увеличенное количество откликов;
- количество откликов можно считать через SQL count, отдельный counter хранить необязательно;
- нельзя разрешать отклик на архивный проект.

### project_tags

```txt
id
name
```

### project_tag_links

```txt
project_id
tag_id
```

Теги не являются критичными для MVP, но можно реализовать, если это не тормозит основные сценарии.

## Связи

```txt
users 1 --- n projects.created_by
users 1 --- n projects.responsible_user_id
projects 1 --- n project_members
users 1 --- n project_members
projects 1 --- n project_responses
users 1 --- n project_responses
users 1 --- n project_responses.processed_by
projects n --- n project_tags
```

## Seed-данные

Добавить seed-данные:

### Пользователи

1. Admin:
   - email: `admin@utmn.ru`
   - full_name: `Администратор ШПИУ`
   - role: `admin`

2. Project manager:
   - email: `manager@utmn.ru`
   - full_name: `Руководитель проекта`
   - role: `project_manager`

3. Employee:
   - email: `employee@utmn.ru`
   - full_name: `Сотрудник ШПИУ`
   - role: `employee`

### Проекты

Создать минимум 5 проектов:
- 3 active;
- 1 paused;
- 1 completed;
- 1 archived, если нужно проверить архив.

Все проекты типа `strategic`.

### Отклики

Создать несколько откликов с разными статусами:
- new;
- viewed;
- contacted;
- accepted;
- rejected.
