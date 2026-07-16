# Local development

```powershell
.\dev.cmd up
.\dev.cmd status
.\dev.cmd test
.\dev.cmd architecture-check
```

`up` selects the `full` Compose profile and exposes only the gateway at
`http://localhost:5173`. Targeted module stacks use Compose profiles directly:

```powershell
docker compose --profile core --profile projects up --build
docker compose --profile core --profile service-desk up --build
```

