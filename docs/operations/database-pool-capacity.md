# Database pool capacity

Date: 2026-07-16

All Python services construct SQLAlchemy engines through
`platform_sdk.database.create_platform_engine`. PostgreSQL connections receive
an explicit `statement_timeout` and low-cardinality `application_name`.

## Long-lived process budget

| Process | Replicas in Compose | Pool | Overflow | Maximum |
| --- | ---: | ---: | ---: | ---: |
| Access API | 1 | 5 | 5 | 10 |
| Projects API | 1 | 5 | 5 | 10 |
| Projects outbox worker | 1 | 2 | 0 | 2 |
| Projects attachment cleanup worker | 1 | 1 | 0 | 1 |
| Service Desk API | 1 | 5 | 5 | 10 |
| Service Desk SLA worker | 1 | 2 | 1 | 3 |
| Service Desk notification worker | 1 | 2 | 1 | 3 |
| Service Desk attachment cleanup worker | 1 | 1 | 0 | 1 |
| Total | 8 | 23 | 17 | 40 |

Migration and seed containers run sequentially before their API and are not
part of steady-state capacity. Production deployment capacity is:

```text
sum(replicas * (pool_size + max_overflow))
```

The result must remain below the PostgreSQL connection budget after reserving
at least 20% for migrations, administration, monitoring and incident response.
Scaling a service therefore requires an explicit pool-budget review.

## Defaults

- `pool_timeout`: 30 seconds
- `pool_recycle`: 1,800 seconds
- `pool_pre_ping`: enabled
- `statement_timeout`: 30,000 ms
- API pools: `5 + 5`
- worker pools: `2 + 1`

The SDK exposes configured capacity plus checked-in, checked-out and overflow
values. Metrics exporters must use `service`, `module`, `process_role` and
`result` labels only; connection IDs, SQL text, user IDs and object IDs are
forbidden labels.

## Alerting

- warn when checked-out connections exceed 80% of configured maximum for five
  minutes;
- page when checkout timeouts occur or saturation exceeds 95%;
- correlate pool saturation with PostgreSQL active connections and statement
  timeout counts;
- do not solve saturation by increasing every module pool independently.
