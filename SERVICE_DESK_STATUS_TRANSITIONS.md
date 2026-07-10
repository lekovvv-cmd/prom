# Переходы статусов Service Desk

Все изменения статуса выполняются через `TicketLifecycleService`. HTTP API использует явные action endpoints; произвольный `PATCH status` не поддерживается.

| From | Action | To | Кто |
|---|---|---|---|
| `draft` | `submit` | `submitted` | заявитель |
| `submitted` | `start_approval` | `pending_approval` | система approval workflow |
| `submitted` | `skip_approval` | `approved` | система для услуги без согласования |
| `pending_approval` | `complete_approval` | `approved` | система после завершения обязательных этапов |
| `pending_approval` | `reject_approval` | `rejected` | согласующий после проверки approval policy |
| `approved` | `assign` | `assigned` | routing/default/manual assignment после проверки capability |
| `assigned`, `in_progress`, `waiting_requester`, `waiting_external` | `reassign` | same status | manager/admin с `service_desk.assign` |
| `assigned` | `start` | `in_progress` | назначенный исполнитель |
| `in_progress` | `request_clarification` | `waiting_requester` | назначенный исполнитель |
| `waiting_requester` | `requester_reply` | `in_progress` | заявитель через публичный ответ |
| `in_progress` | `wait_external` | `waiting_external` | назначенный исполнитель |
| `waiting_external` | `resume` | `in_progress` | назначенный исполнитель |
| `in_progress` | `resolve` | `resolved` | назначенный исполнитель |
| `resolved` | `close` | `closed` | заявитель, исполнитель или Service Desk admin |
| допустимые незавершённые статусы | `cancel` | `cancelled` | заявитель до `approved`; Service Desk admin — до `resolved` |

Обязательные payload:

- `request_clarification`: `comment`;
- `wait_external`: `reason`;
- `reject_approval`: `comment`;
- `resolve`: `resolution_summary`;
- `cancel`: `reason`.

Каждый переход атомарно обновляет статус и связанный timestamp, затем добавляет неизменяемую запись history с `from_status`, `to_status` и данными действия.
