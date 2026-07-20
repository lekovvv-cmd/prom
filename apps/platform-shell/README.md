# Platform shell

The shell owns platform navigation, authentication/session providers, module
registration, routing, and shared layout. Projects and Service Desk UI code is
owned by their packages under `apps/*/frontend`.

Install and run a frontend-only development server from the repository root:

```bash
npm ci
npm run dev --workspace=@prom/platform-shell
```

Run the production-like platform locally:

```powershell
.\dev.ps1 up
.\dev.ps1 test-e2e
```

```bash
./dev.sh up
./dev.sh test-e2e
```

Playwright targets `E2E_BASE_URL` when set and otherwise uses
`http://127.0.0.1:5173`. The full CI job starts `compose.yaml` with the `full`
profile before invoking the same `npm run test:e2e` command.
