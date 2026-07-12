# Текущее состояние

## Реализовано

Service Desk включает закрытый каталог, динамические формы и черновики, заявки, согласования, назначения, комментарии, вложения, SLA, уведомления, Workbench, аналитику и административную конфигурацию. Корень `/` является публичным selector Projects/Service Desk, а защищённые маршруты используют общий JWT Projects.

## Исправлено corrective stage

- Локальный identity bootstrap синхронизирует реальные Projects UUID по email без runtime-связи баз.
- Создание и отправка заявки требуют `service_desk.create_request`.
- Добавлена ручная смена приоритета с причиной, row lock и событием `priority_changed`.
- Терминальные статусы исключены из активного backlog и нагрузки исполнителей.
- `/health/ready` проверяет Service Desk DB и writable storage; `/health/live` не зависит от БД.
- Последнего активного `service_desk_admin` нельзя деактивировать или понизить.
- Production renderer переиспользуется в admin preview; массивы условий и настройки draft-версии доступны в UI.
- Вложения draft можно удалять с удалением metadata, binary и записью history.
- Комментарии можно редактировать и удалять в UI согласно backend policy.
- Полная платформа описана в Docker Compose; host Python/Node не требуются.
- Docker smoke пройден на чистых и существующих volumes; restart backend/worker сохраняет вложения.

## Архитектурные решения

Projects DB и Service Desk DB остаются раздельными. Service Desk backend не импортирует Projects ORM и не обращается к Projects DB во время API requests. Identity repair выполняется только bootstrap job. SLA worker работает отдельным процессом. Локальные вложения хранятся в отдельном persistent volume.

## BLOCKED_EXTERNAL

- Корпоративное SSO требует внешней интеграции.
- Email delivery требует реального почтового канала; outbox email остаётся `blocked_external`.

## Deferred

- `platform_admin` и полноценный platform-wide IAM.
- Отдельный Prometheus/Grafana observability stack и `/metrics`.
- Тяжёлый rich text editor; enum `rich_text` отображается как многострочный текст.

## Открытые вопросы

- Публичный каталог не включён: Service Desk и формы требуют `service_desk.access`.
- Решение о production storage provider принимается перед промышленным развёртыванием.
