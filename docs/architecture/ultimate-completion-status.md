# ULTIMATE completion status

Updated: 2026-07-22

| Area | Status | Evidence / next action |
| --- | --- | --- |
| Baseline | DONE | See `ultimate-completion-baseline.md`. |
| Legacy identity migration | IN_PROGRESS | First implementation phase per completion prompt. |
| Dynamic Access modules | TODO | Audit current hard-coded module behavior and add registration workflow. |
| Group RBAC and role integrity | TODO | Wire group roles into effective permissions and add mutation behavior/tests. |
| Mock login contract | TODO | Verify backend-only local/test enforcement. |
| JWKS key rotation | TODO | Add persisted key ring, overlap, retirement, and tests. |
| Secure browser session | TODO | Replace privileged browser token persistence with cookie session + CSRF. |
| Projects application layer and UoW | TODO | Split command/query/membership/recommendation concerns and move transaction boundaries. |
| Transaction-safe files | TODO | Verify upload lifecycle and move physical deletion behind committed outbox work. |
| Tailwind/style migration | TODO | Remove giant product CSS and satisfy style boundaries. |
| Generic shared API client | TODO | Remove module vocabulary/formatting and preserve structured Problem Details. |
| Module generator | TODO | Complete platform registration and atomic acceptance workflow. |
| Repository cleanup | TODO | Remove generated/runtime artifacts safely and document dead-code review. |
| Required CI coverage | TODO | Add/verify migration, RBAC, rotation, storage, style, generator, Compose, security jobs. |
| Clean Compose and persistence | TODO | Reproduce on new volumes, then verify restart persistence. |
| Full regression and E2E | TODO | Run exact final command set and gateway role/security scenarios. |
| Final report and logical commits | TODO | Produce evidence table and verdict without merging `main`. |

