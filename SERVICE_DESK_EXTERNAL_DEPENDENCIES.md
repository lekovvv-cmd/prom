# Service Desk external dependencies

## Corporate SSO — BLOCKED_EXTERNAL

Локальный demo login использует код `000000`. Подключение production SSO требует metadata,
client credentials, redirect/logout URLs, group/role mapping, key rotation и требований ЦИТ.
Frontend headers или query parameters не используются как источник ролей: до интеграции доверие
основано только на JWT, подписанном Projects backend.

## Email delivery — BLOCKED_EXTERNAL

Service Desk сохраняет каждое намерение email-доставки в notification outbox со статусом
`blocked_external`. In-app доставка работает независимо. Email не считается отправленным и не
переводится в `sent`, пока ЦИТ не предоставит и не согласует реальную интеграцию.

Для разблокировки необходимы подтверждённые ЦИТ данные и требования:

- SMTP server и port либо документированный API endpoint и protocol;
- разрешённый sender address/display name и правила envelope sender;
- authentication mechanism и утверждённый способ безопасного предоставления/rotation credentials;
- перечень разрешённых recipient domains/groups и ограничения на внешних получателей;
- retry policy restrictions, включая допустимые интервалы, максимальное число попыток и обработку permanent failures;
- rate limits, burst limits и допустимая параллельность;
- требования ЦИТ по TLS, certificate validation, network allowlists, audit/log retention и защите персональных данных.

Значения этих параметров в репозитории отсутствуют: они не должны угадываться, подменяться fake
SMTP или оформляться как успешная доставка до фактического подключения и проверки канала.

Prometheus `/metrics`, Grafana и fake email delivery намеренно не являются внешними blockers:
они исключены из текущего scope.
