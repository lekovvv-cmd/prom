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
Stage 8.2: добавлен authenticated API списка/unread count/read/read-all, полностью scoped через CurrentServiceDeskUser, с idempotent read_at и запретом доступа к foreign notifications.
Stage 8.3: в PROM Header добавлен responsive notification center с badge, loading/error/empty states, read/read-all, ticket navigation и безопасным отображением событий без ticket_id; добавлены frontend и browser E2E проверки.
Stage 8.4: добавлен actor-aware backend read model contextual counters и PROM navigation counters для моих согласований, назначений, ожидающих ответа и capability-gated SLA breaches без клиентского пересчёта tickets.
Stage 8.5: добавлен transactional ServiceDeskNotificationOutbox, уникальная event/channel/recipient идемпотентность и lock-based retry worker; in-app outbox и notification фиксируются атомарно без промежутка best-effort после business commit.
Stage 8.6: EmailChannel сохраняет delivery intents как blocked_external и никогда не имитирует отправку; retry worker оставляет их заблокированными, InAppChannel продолжает доставку; требования к реальной ЦИТ интеграции записаны в SERVICE_DESK_EXTERNAL_DEPENDENCIES.md.
Stage 8 CI checkpoint: Service Desk migrations/seed, 94 pytest и ruff; Projects migrations/seed и 16 pytest; frontend 51 tests/build; browser E2E Service Desk + Projects (3/3) пройдены. Regression flows notification badge/read-all/ticket navigation, approval и SLA admin green; lifecycle/assignment/requester reply/SLA warning-breach покрыты backend suite.
Stage 8 CI regression fixes: стабилизированы imports notification tests для чистого CI environment; общий FastAPI constraint обновлён до Python 3.14-compatible 0.136.x, после чего deprecated asyncio.iscoroutinefunction warnings устранены без suppression (Service Desk 94/94 и Projects 16/16 без warning summary).
Stage 8 review: исправлена доставка approval_requested при активации каждого следующего этапа многоэтапного workflow и доступность notification center для Projects admin с профилем Service Desk; добавлены backend/frontend regression tests (Service Desk 94/94, frontend 52/52, ruff и build green).
Stage 9.1: добавлен policy-guarded Workbench ticket query с contextual visibility, защитой чужих drafts, SQL-фильтрами/search, bounded stable pagination и lightweight row read model.
Stage 9.2: добавлены actor-aware quick views/counters с общими server-side predicates, active approval/assignment semantics, resolved без closed и capability-gated SLA breach view.
Stage 9.3: добавлены PROM Workbench route/navigation, filters/table/action dialogs, read-only user options и eligible assignees; lifecycle authorization и backend allowed_actions сведены к общей TicketPolicyService.
Stage 9.4: добавлен единый server-computed SLA summary для filter/overdue/quick view/table, pause-aware overdue, batch-loading SLA context и текстовые PROM SLA indicators с active metric/due_at.
Stage 9 regression checks: Service Desk 101 pytest и ruff; Projects 16 pytest; frontend 58 tests и build; CI browser E2E Projects + Service Desk, включая Workbench manager assign → assignee start → resolve, пройдены.
Stage 10 final UI closure: Service Desk admin pages используют scoped persistent navigation с canonical `/admin/service-desk/*` routes и backward-compatible redirects; опасные access mutations подтверждаются PROM Modal, а access edit modal закрывается только после успешной mutation.
Stage 8 closure: добавлена явная channel policy для SLA escalation, route-aware contextual counters с invalidation/eventual refresh, metric/threshold-aware SLA notification copy, bounded notification/outbox reads и честный one-shot operational contract для outbox scheduler; targeted notification/SLA checks и CI run 29145060881 green.
Stage 9 review/closure: Workbench SLA state now uses current active SLA metric instead of historical escalation existence; first_response and resolution pause/overdue semantics are metric-specific and aligned with the SLA worker; Workbench refreshes on shared Service Desk invalidation and periodic polling without resetting filters; frontend status filter includes submitted/rejected/cancelled non-draft statuses. Checks: Service Desk pytest 112/112 passed, service-desk ruff passed, frontend tests 64/64 passed, frontend build passed. E2E was not run for this closure.
Stage 10 review/closure: SLA compliance now uses same completed-obligation cohorts while breach event counters keep period-event semantics; Stage 10 near-breach analytics reuses the Stage 9 current SLA projection; assignee analytics was changed from per-user query loops to bounded set-based aggregation; dashboard filters now include date/category/service/assignee/priority and reuse one canonical params builder for all analytics requests; visible Service Desk admin navigation was reduced to real guarded routes; access administration now supports filters, pagination, profile/access-type edit, canonical PUT-only capability changes, modal activation/deactivation, self-access refresh, and consistent create/update validation. Checks: Service Desk pytest 115/115 passed; Service Desk ruff passed; Projects pytest 16/16 passed; frontend tests 66/66 passed; frontend build passed. Alembic migration checks timed out because local Postgres/Docker was unavailable; browser E2E and GitHub Actions were not run.
Stage 10 Docker checkpoint update: after Docker was started, service_desk_db was created and became healthy; Service Desk alembic upgrade/current reached 202607110023 head and seed completed successfully; Projects alembic current reached 202607060001 head and seed completed successfully.
Stage 9 closure round 2: Workbench pagination now separates page changes from filter resets; persistent SLA breaches are projected consistently across row summaries, sla_state filters, overdue/quick views and counters, including terminal tickets; Workbench deadline boundaries use due_at <= now to match the SLA worker; background refresh/invalidation is silent and keeps existing rows on refresh errors. Checks: Service Desk pytest 119/119 passed; Service Desk ruff passed; Workbench/SLA targeted pytest 15/15 passed; frontend tests 72/72 passed; frontend build passed. Browser E2E and GitHub Actions were not run.
Final completion F1: unified Service Desk admin shell for dashboard/access/routing/SLA/tickets, module-aware Header with Russian Service Desk navigation and module switcher, centralized visible ticket labels, and removed decorative `/metrics`; frontend build and targeted Header/admin notification tests passed.
Final completion F2: добавлен публичный каталог `/service-desk`, страницы услуги и generic dynamic form с visibility/required rules, типами полей и file uploads; реализованы раздельные сохранение черновика/отправка с backend validation mapping и «Мои заявки» с фильтрами. Frontend tests 72/72 и build passed.
