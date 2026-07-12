# Текущее состояние

## Реализовано

Service Desk включает закрытый каталог, динамические формы и черновики, заявки, согласования, назначения, комментарии, вложения, SLA, уведомления, Workbench, аналитику и административную конфигурацию. Корень `/` является публичным selector Projects/Service Desk, а защищённые маршруты используют общий JWT Projects.

## Исправлено corrective stage

- Локальный identity bootstrap синхронизирует реальные Projects UUID по email без runtime-связи баз.
- Активная Service Desk role включает вход, draft и submit; `service_desk.access` и
  `service_desk.create_request` не являются редактируемыми capabilities.
- Добавлена ручная смена приоритета с причиной, row lock и событием `priority_changed`.
- Терминальные статусы исключены из активного backlog и нагрузки исполнителей.
- `/health/ready` проверяет Service Desk DB и writable storage; `/health/live` не зависит от БД.
- Последнего активного `service_desk_admin` нельзя деактивировать или понизить.
- Platform roles мигрированы в `employee`, `project_manager`, `platform_admin`; Service Desk
  roles — `service_desk_manager`, `service_desk_admin`.
- `platform_admin` получает полный Service Desk bypass по подписанному JWT без заранее созданного
  локального profile.
- Catalog/form API и `/service-desk/**`, `/admin/service-desk/**` закрыты; frontend использует
  безопасный access-status probe вместо глобального `/me → 403`.
- Identity bootstrap является единственным profile writer, заменяет capabilities и чинит старые
  email/UUID profiles; catalog seed не создаёт identities.
- Demo users: `employee@utmn.ru`, `project.manager@utmn.ru`, `sd.manager@utmn.ru`,
  `sd.admin@utmn.ru`, `admin@utmn.ru`; код `000000`.
- Production renderer переиспользуется в admin preview; массивы условий и настройки draft-версии доступны в UI.
- Вложения draft можно удалять с удалением metadata, binary и записью history.
- Комментарии можно редактировать и удалять в UI согласно backend policy.
- Полная платформа описана в Docker Compose; host Python/Node не требуются.
- Compose разделяет migrations, Projects seed, platform bootstrap и Service Desk seed; wrappers
  используют `docker compose up --build -d --wait` и печатают URL только после readiness.

## Архитектурные решения

Projects DB и Service Desk DB остаются раздельными. Service Desk backend не импортирует Projects ORM и не обращается к Projects DB во время API requests. Identity repair выполняется только bootstrap job. SLA worker работает отдельным процессом. Локальные вложения хранятся в отдельном persistent volume.

## BLOCKED_EXTERNAL

- Корпоративное SSO требует внешней интеграции.
- Email delivery требует реального почтового канала; outbox email остаётся `blocked_external`.

## Deferred / не входит в поставку

- Внешний production IAM/SSO поверх реализованного локального `platform_admin`.
- Prometheus/Grafana и `/metrics` не входят в scope и не должны возвращаться.
- Тяжёлый rich text editor; enum `rich_text` отображается как многострочный текст.

## Открытые вопросы

- Публичный каталог не включён: Service Desk и формы требуют активную SD role либо
  `platform_admin`; отдельной capability для входа нет.
- Решение о production storage provider принимается перед промышленным развёртыванием.

## Фактически выполненные проверки текущего stabilization этапа

- Projects pytest: `17 passed`.
- Service Desk pytest: `138 passed, 1 skipped`.
- Frontend Vitest: `82 passed`; TypeScript/Vite build успешен.
- Ruff: успешно.
- Clean SQLite Alembic chains: успешно до `202607120003` и `202607120026`.
- Playwright discovery: `12 tests`.
- Обновлённый production Compose E2E: не выполнен локально из-за недоступного Docker socket;
  не считать этот пункт зелёным до фактического прогона.
