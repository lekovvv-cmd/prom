# Утверждённые шаблоны Service Desk

Реализация соответствует самодостаточному ТЗ
`PROM_TZ_11_APPROVED_SERVICE_DESK_TEMPLATES.md`.

- Revision: `approved-11-v1`
- Seed source marker: `PROM_TZ_11_APPROVED_SERVICE_DESK_TEMPLATES.md`
- Все версии ниже создаются seed/sync с `_seed_generated: true`.
- При обновлении старая seed-версия архивируется; заявки продолжают ссылаться на её
  `template_version_id`. Ручная опубликованная версия не перезаписывается: создаётся
  черновик утверждённой revision и записывается предупреждение в лог.

## Templates

| Service | Category/title in DB | Aliases | TZ | Fields (key: type, required, dictionary) | Status |
|---|---|---|---|---|---|
| Заказ воды | `ГИА: Администрирование` / `Заказ воды` | `Заказ воды (ГИА)` | 5.1 | `bottle_count: number, yes, min=1`; `bottle_volume: text, yes`; `water_type: select, yes, water_type`; `event_starts_at: datetime, yes`; `event_ends_at: datetime, yes`; `commission_members_count: number, yes, min=1`; `gia_sessions_count: number, yes, min=1`; `graduating_students_count: number, yes, min=1` | READY |
| Установка камер | `ГИА: Администрирование` / `Установка камер` | `Установка камер (ГИА)` | 5.2 | `institute: select, yes, institutes, default=ШПИУ`; `gia_type: select, yes, gia_type`; `study_direction: select, yes, study_directions`; `installation_address: select, yes, camera_installation_addresses, default=Ленина 38`; `room_number: text, yes`; `event_starts_at: datetime, yes`; `event_ends_at: datetime, yes`; `comment: textarea, no` | READY |
| Бронирование аудиторий | `Административно-хозяйственное сопровождение` / `Бронирование аудиторий` | — | 5.3 | `booking_purpose: textarea, yes`; `approved_with_full_name: text, yes`; `building_address: select, yes, building_addresses`; `room_number: text, yes`; `event_starts_at: datetime, yes`; `event_ends_at: datetime, yes`; `comment: textarea, no` | READY |
| На печать в Издательство | `Административно-хозяйственное сопровождение` / `На печать в Издательство` | — | 5.4 | `event_name: text, yes`; `publisher_approval_status: select, yes, publisher_approval_status`; `product_type: text, yes`; `production_due_date: date, yes`; `product_quantity: number, yes, min=1`; `template_link: text, yes`; `additional_characteristics: textarea, no` | READY |
| Роль табельщика (табель рабочего времени, график отпусков) | `Административно-хозяйственное сопровождение` / same | `Роль табельщика` | 5.5 | `employee_full_name: text, yes`; `vacation_starts_on: date, yes`; `vacation_ends_on: date, yes` | BUSINESS_AMBIGUITY |
| Ввоз (вывоз) и внос (вынос) материальных ценностей | `Административно-хозяйственное сопровождение` / same | `Ввоз/вывоз и внос/вынос материальных ценностей` | 5.6 | `event_name: text, yes`; `movement_starts_at: datetime, yes`; `movement_ends_at: datetime, yes`; `inventory_list_file: file, yes`; `material_type: text, yes`; `packaging: text, yes`; `vehicle_details: text, yes` | READY |
| Допуск в здание | `Административно-хозяйственное сопровождение` / `Допуск в здание` | — | 5.7 | `person_full_name: textarea, yes`; `equipment: textarea, no`; `address: text, yes`; `access_starts_on: date, yes`; `access_ends_on: date, yes` | READY |
| Транспортное обслуживание | `Административно-хозяйственное сопровождение` / same | — | 5.8 | `event_name: text, yes`; `people_count: number, yes, min=1`; `students_count: number, yes, min=1`; `event_starts_at: datetime, yes`; `event_ends_at: datetime, yes`; `route: textarea, yes` | READY |
| Оформление и регистрация исходящего документа | `Административно-хозяйственное сопровождение` / same | `Регистрация исходящего документа` | 5.9 | `document: text, yes`; `document_file: file, yes` | BUSINESS_AMBIGUITY |
| График отпусков | `Административно-хозяйственное сопровождение` / `График отпусков` | — | 5.10 | `employee_full_name: text, yes`; `vacation_starts_on: date, yes`; `vacation_ends_on: date, yes` | BUSINESS_AMBIGUITY |
| Получение со склада (кроме компьютерной техники) | `Административно-хозяйственное сопровождение` / same | `Получение со склада (не компьютерная техника)`; `Получение со склада` | 5.11 | `materially_responsible_person: text, yes`; `position: text, yes`; `event_name: text, yes`; `inventory_list_file: file, yes` | READY |

## Dictionaries

| Code | Values | Status |
|---|---|---|
| `building_addresses` | Ленина 16; Ленина 23; Ленина 38; Перекопская 15; Республики 9; Другое (укажите в комментарии) | READY |
| `water_type` | Газированная; Негазированная; Другое | READY |
| `gia_type` | гос.экзамен; ВКР | READY |
| `institutes` | ШПИУ | READY — локально управляемый справочник, доступный для расширения через admin UI |
| `study_directions` | 8 локальных направлений из раздела 4.6 ТЗ | BUSINESS_AMBIGUITY |
| `publisher_approval_status` | Согласовано; Не согласовано | READY |

## Known business ambiguities and source gaps

1. **Роль табельщика / График отпусков.** Архив не содержит отдельного набора полей
   для предоставления роли табельщика; видимая форма «Табель» содержит поля графика
   отпуска. До решения владельца процесса обе официальные услуги используют
   подтверждённую схему `ФИО`, `Дата начала отпуска`, `Дата окончания отпуска`.
   Они не объединяются и не удаляются автоматически.
2. **SOURCE_GAP:** варианты старого списка «Документ» отсутствуют в предоставленном
   архиве. Поэтому поле реализовано как обязательное `text` с label `Документ`; новый
   справочник типов документов не создавался.
3. **Локальный список направлений.** `study_directions` — неполный локальный набор,
   а не интеграция со справочниками ТюмГУ.
4. **Интеграция ТюмГУ отсутствует.** SSO, email delivery и внешние справочники не
   представлены этой задачей как реализованные.
5. **Дубликат бронирования.** Официальная форма используется только для услуги в
   категории `Административно-хозяйственное сопровождение`. Одноимённая услуга в
   `Сопровождение учебного процесса` не изменяется и не удаляется автоматически.
