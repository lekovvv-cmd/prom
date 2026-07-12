# Browser QA findings

## BUG-001: Docker frontend build ломался на WSL при наличии `node_modules`

- Story / Severity / Role / Route: US-0.1 / High / all / Docker bootstrap.
- Preconditions / Steps: WSL checkout с установленными frontend dependencies; `docker compose up --build` через Docker Desktop.
- Expected / Actual: build context должен собираться; Docker завершался с `invalid file request node_modules/.bin/nanoid`.
- Console / Network / Evidence: BuildKit output; frontend context до исправления около 125.8 MB.
- Root cause / Owner layer: отсутствовал `frontend/.dockerignore`; Docker/WSL пытался передать host `node_modules` с несовместимыми symlink wrappers. Owner: Docker.
- Fix / Regression test / Exact retest: добавлен `.dockerignore`; clean `down -v && up --build -d --wait`, context 30.61 kB в финальной сборке, frontend healthy.
- Status: FIXED

## BUG-002: чистый Service Desk seed падал без таблицы пользователя в metadata

- Story / Severity / Role / Route: US-0.1 / High / all / seed/bootstrap.
- Preconditions / Steps: пустая БД, standalone `python scripts/seed.py`.
- Expected / Actual: seed создаёт demo catalog/forms; SQLAlchemy выдавал `NoReferencedTableError: service_desk_users`.
- Console / Network / Evidence: isolated subprocess reproduction.
- Root cause / Owner layer: seed импортировал catalog/templates, но не регистрировал access models, на которые ссылаются FK. Owner: seed/bootstrap.
- Fix / Regression test / Exact retest: явный import access models; `tests/test_seed.py::test_seed_script_registers_referenced_user_table_in_isolated_process`; два clean Docker bootstrap прошли.
- Status: FIXED

## BUG-003: вложения Projects возвращали 500 в production container

- Story / Severity / Role / Route: US-3, US-0.2 / High / project manager, employee / Projects create/respond.
- Preconditions / Steps: создать проект с файлами через UI.
- Expected / Actual: файлы сохраняются; backend отвечал 500 `PermissionError: /app/storage`.
- Console / Network / Evidence: network 500 и backend traceback; exact browser flow в `e2e/mvp.spec.ts`.
- Root cause / Owner layer: непривилегированный runtime-user не имел writable persistent storage. Owner: Docker/backend storage.
- Fix / Regression test / Exact retest: writable `/app/storage/projects`, `UPLOADS_DIR`, named volume `projects_storage`; MVP browser flow проходит, 3 файла сохранились после `down/up` и restart.
- Status: FIXED

## BUG-004: readiness Projects не проверял DB/storage, БД не восстанавливались после Docker restart

- Story / Severity / Role / Route: US-0.1–0.3 / High / all / `/api/health`.
- Preconditions / Steps: остановить/перезапустить Docker engine или DB container.
- Expected / Actual: unhealthy до восстановления зависимостей; API сообщал healthy при недоступной БД, DB containers оставались stopped.
- Console / Network / Evidence: compose state и false-positive health response.
- Root cause / Owner layer: health endpoint был статическим, у DB отсутствовал restart policy. Owner: Docker/backend.
- Fix / Regression test / Exact retest: health делает `SELECT 1` и marker write; DB получили `restart: unless-stopped`; `test_health_checks_database_and_upload_storage`; final clean/restart smoke healthy.
- Status: FIXED

## BUG-005: деактивация элемента каталога не обновляла UI

- Story / Severity / Role / Route: US-15 / Medium / SD admin / `/admin/service-desk/catalog`.
- Preconditions / Steps: нажать деактивацию категории/услуги.
- Expected / Actual: видимое состояние меняется после успешного ответа; UI оставался в старом состоянии.
- Console / Network / Evidence: mutation 200, stale DOM; `e2e/service-desk-admin-catalog.spec.ts`.
- Root cause / Owner layer: promise результата API игнорировался, reload данных не ожидался. Owner: frontend.
- Fix / Regression test / Exact retest: единый awaited `toggleCatalogItem`, error handling и reload; полный catalog CRUD browser test проходит.
- Status: FIXED

## BUG-006: каталог принимал дублирующиеся нормализованные названия

- Story / Severity / Role / Route: US-15 / Medium / SD admin / catalog API and UI.
- Preconditions / Steps: создать category/service с тем же title в другом регистре/с пробелами.
- Expected / Actual: понятный 409; создавался дубликат.
- Console / Network / Evidence: browser POST и DOM; catalog test допускает только ожидаемый 409.
- Root cause / Owner layer: не было scoped normalized validation и DB constraint. Owner: backend/DB.
- Fix / Regression test / Exact retest: repository/service checks, race-safe `IntegrityError`, migration `202607120027` с дедупликацией и expression indexes; `tests/test_catalog.py`; browser catalog CRUD PASS.
- Status: FIXED

## BUG-007: approval mutation возвращала устаревший workflow

- Story / Severity / Role / Route: US-8.1 / High / SD admin / `/admin/service-desk/approvals`.
- Preconditions / Steps: production session `expire_on_commit=False`, добавить/изменить stage через UI.
- Expected / Actual: новый stage сразу появляется; POST был 201, но response relationship содержал прежний список.
- Console / Network / Evidence: successful mutation и пустой/stale stage list; approval browser trace во время воспроизведения.
- Root cause / Owner layer: identity map сохранял загруженную relationship после commit. Owner: backend/SQLAlchemy repository.
- Fix / Regression test / Exact retest: `populate_existing=True`; `test_stage_mutation_response_is_fresh_when_sessions_do_not_expire_on_commit`; полный UI CRUD stage/approver/edit/delete/disable PASS.
- Status: FIXED

## BUG-008: API client пытался разобрать пустой 204 как JSON

- Story / Severity / Role / Route: US-8.1, US-18 / Medium / SD admin / DELETE mutations.
- Preconditions / Steps: удалить approval stage или routing rule; backend возвращает 204 с JSON content-type.
- Expected / Actual: успешное удаление; UI показывал `Unexpected end of JSON input`, объект оставался в DOM.
- Console / Network / Evidence: DELETE 204 и browser alert; approval workflow exact reproduction.
- Root cause / Owner layer: `parseResponse` проверял content-type до status 204. Owner: frontend shared API.
- Fix / Regression test / Exact retest: обработка 204 до JSON parsing; unit test с JSON content-type; approval и routing delete browser flows PASS.
- Status: FIXED

## BUG-009: справочник позволял duplicate item value

- Story / Severity / Role / Route: US-17 / Medium / SD admin / `/admin/service-desk/dictionaries`.
- Preconditions / Steps: добавить два item с одинаковым `value`.
- Expected / Actual: 409 validation; оба значения создавались с 201.
- Console / Network / Evidence: DOM содержал две строки с одинаковым value, backend logs — два POST 201.
- Root cause / Owner layer: отсутствовали normalized uniqueness check и DB constraint. Owner: backend/DB.
- Fix / Regression test / Exact retest: service/repository validation, race-safe handling, migration `202607120028` с дедупликацией и unique expression index; `test_dictionary_item_values_are_unique_within_dictionary`; exact dictionary UI CRUD/409/reload PASS.
- Status: FIXED
