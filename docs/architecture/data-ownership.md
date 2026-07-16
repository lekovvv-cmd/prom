# Data ownership

Access owns `access_db`; Projects owns `projects_db`; Service Desk owns
`service_desk_db`. Each has separate credentials, migrations, and runtime
connections. Direct cross-database SQL, ORM imports, and joins are forbidden.
Integration uses published HTTP contracts or transactional outbox events.

