# Frontend style migration report

Date: 2026-07-22

## Result

The platform shell and both product frontends now use Tailwind CSS as the utility
engine, a small shared component layer in `@prom/ui`, product-scoped theme tokens,
and lazy product style entry points. The previous product-wide monolithic style
files were removed.

Complex component-local behavior is isolated where it improves ownership. For
example, `Spinner.tsx` owns its layout and animation through the adjacent
`Spinner.module.css`. Shared primitives remain in the deliberately small
`@prom/ui` layers, while product-specific selectors live only under their product
style entry points.

## Source metrics

| Metric | Before | After |
| --- | ---: | ---: |
| CSS files measured | 6 | 33 |
| Total source lines | 5,999 | 5,935 |
| Total source bytes | 102,417 | 104,046 |
| Largest stylesheet | 2,392 lines | 274 lines |
| Shell global stylesheet | 91 lines | 86 lines |
| Raw color declarations | 254 | 169, all in theme/token files |
| `!important` declarations | 6 | 0 |
| Statically unused selectors | not enforced | 0 |
| Boundary warnings | not enforced | 0 |

The slight byte increase comes from named semantic tokens and explicit import
boundaries. It replaces hidden duplication with reviewable ownership while
reducing the largest file by 88.5%.

## Delivery budgets

The production build passed all configured budgets:

| Asset | Result | Budget |
| --- | ---: | ---: |
| Initial JavaScript | 273,465 bytes | 300,000 bytes |
| Initial CSS | 27,817 bytes | 30,000 bytes |
| Largest lazy JavaScript chunk | 46,972 bytes | 60,000 bytes |
| Largest lazy CSS chunk | 44,017 bytes | 45,000 bytes |

Product CSS remains lazy: Projects ships in a 24.71 kB route chunk and Service
Desk in a 44.01 kB route chunk rather than inflating the initial shell bundle.

## Automated guardrails

`npm run check:styles` recursively checks every CSS file and fails on:

- an oversized global file or component stylesheet;
- reintroduction of the retired monolithic product files;
- raw colors outside theme/token files;
- undocumented `!important` declarations;
- product-level redefinitions of shared primitives;
- selectors that are not referenced by application code.

The check is part of the `frontend-tests` CI job. `npm run build:check` separately
enforces production bundle budgets in `frontend-build`.

## Verification

- `npm run check:styles` — passed, 0 warnings.
- `npm run typecheck` — passed.
- `npm run lint` — passed.
- `npm run test` — passed, 40 files / 109 tests.
- `npm run build:check` — passed with the budgets above.
