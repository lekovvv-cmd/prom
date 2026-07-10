Stage 1.1: создан отдельный service-desk-backend с FastAPI health и metrics endpoints.
Stage 1.2: добавлена отдельная Service Desk DB-конфигурация, SQLAlchemy Base и Alembic-миграция доступа.
Stage 1.3: добавлен отдельный CI job для Service Desk backend с миграциями, pytest и ruff.
Stage 1.4: добавлен frontend Service Desk API client с отдельным base URL и общим token storage.
Stage 1.5: добавлена dev-инфраструктура Service Desk DB/env для локального запуска.
Stage 2.1: добавлены Service Desk категории/услуги каталога с public/admin API и миграцией.
Stage 2.2: добавлены версионированные шаблоны услуг с draft/published/archived API.
Stage 2.3: добавлены dynamic поля шаблонов и справочники Service Desk.
Stage 2.4: добавлена backend-валидация dynamic форм с conditional visibility/required rules.
Stage 2.5: добавлен preview шаблона с resolved options из inline values и справочников.
Stage 2.6: добавлен idempotent seed каталога/справочников/шаблонов Service Desk из ТЗ и скриншотов.
Stage 3.1: добавлены draft-заявки Service Desk со списком, деталями, редактированием и history.
Stage 3.2: добавлена отправка draft с backend-валидацией формы и concurrency-safe номером SD-YYYY-NNNNNN.
Stage 3.3 partial: backend ticket details и `/me/tickets` list реализованы; frontend details добавлен, отдельный frontend ticket list отсутствует.
Stage 3.4: добавлена единая lifecycle state machine с action endpoints, timestamps, причинами и immutable history.
Stage 3.5: добавлены history read model и timeline истории на frontend ticket details.
Stage 4.1: добавлена настройка approval workflow на draft-шаблоне с этапами ANY/ALL и согласующими.
Stage 4.2: добавлен immutable snapshot approval workflow в заявку при submit и автопереход по approval mode.
Stage 4.3–4.4: добавлены approve/reject решения, ANY/ALL evaluation и multi-stage progression со skip логикой.
Stage 4.5 prerequisite: добавлены JWT access bridge, Service Desk `/me` capabilities и связанные dev user projections.
Stage 4.5: добавлены backend `allowed_actions`, защищённые approval actions, карточка согласования и Service Desk browser E2E.
Stage 5.1: добавлены JWT-защищённые manual assign/reassign с проверкой capability исполнителя и history assignment_source.
Stage 5.2: добавлен default assignment на услуге/версии шаблона с проверкой active/be_assignee и history assignment_source=default.
Stage 5.3: добавлены routing rules с capability manage_routing, priority evaluation, routing snapshot и действиями assign_user/set_priority.
Stage 5.4: добавлен capability-guarded UI маршрутизации с CRUD/reorder правил, condition/action builder и выбором eligible исполнителей.
Stage 6.1: добавлены public/internal комментарии с soft-delete audit, фильтрацией internal для requester и auto requester_reply из waiting_requester.
Stage 6.2: добавлены private local-storage вложения ticket/comment с owner metadata, MIME/extension/size/count validation и visibility-aware API.
Stage 6.3: добавлены вложения dynamic file-полей с привязкой к ключу шаблона, field-level validation и проверкой required file по фактическим metadata при submit.
Stage 6.4: добавлено JWT-защищённое скачивание вложений с проверкой доступа к ticket и отдельной защитой internal comment files.
Stage 7.1: добавлены SLA business calendars с IANA timezone, несколькими непересекающимися рабочими интервалами и capability-защищённым admin API.
Stage 7.2: добавлены SLA calendar exceptions типов holiday/working_day/custom_hours с атомарным управлением через calendar API и проверкой непротиворечивых интервалов на дату.
Stage 7.3: добавлены SLA policies и приоритетные bindings по версии шаблона/service/category/priority/field value, admin API и immutable SLA snapshot заявки при submit.
Stage 7.4: добавлен timezone-aware business-time SLA engine с weekly intervals, breaks, calendar exceptions, DST/UTC conversion и расчётом first response/resolution due из immutable snapshot.
Stage 7.5: добавлены policy-specific pause statuses, concurrency-safe SLA pause periods, lifecycle pause/resume, накопление paused time, business-time recalculation и auditable history; first response фиксируется по start/request clarification/public assignee comment.
Stage 7.6: добавлен независимый idempotent SLA breach worker/CLI с row locking, active-pause filtering, response/resolution state и audit events.
Stage 7.7: добавлены SLA escalation rules с произвольными thresholds, всеми recipient/action types и idempotent durable events для будущей notification delivery без fake email status.
Stage 7.8: добавлен capability-guarded PROM SLA admin UI для calendars/hours, policies/durations/pause statuses, bindings и escalation rules.
Stage 7 CI checkpoint: Service Desk migrations/seed, pytest, ruff, frontend tests/build и browser E2E (Service Desk + Projects MVP) пройдены; GitHub Actions green.
Stage 8.1: добавлен собственный Service Desk notification domain с типизированными событиями, server-side recipient selection, транзакционным InAppChannel и интеграцией lifecycle/approval/assignment/comments/SLA; duplicate delivery одного event защищена уникальным ключом.
