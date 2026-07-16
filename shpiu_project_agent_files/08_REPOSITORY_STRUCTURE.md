# 08_REPOSITORY_STRUCTURE.md — желаемая структура репозитория

```txt
project-showcase/
  README.md
  docker-compose.yml
  .gitignore

  backend/
    README.md
    .env.example
    pyproject.toml
    alembic.ini

    app/
      __init__.py
      main.py

      api/
        __init__.py
        deps.py
        router.py
        routes/
          __init__.py
          auth.py
          projects.py
          admin_projects.py
          admin_responses.py
          admin_stats.py

      core/
        __init__.py
        config.py
        database.py
        security.py
        enums.py
        pagination.py
        exceptions.py
        schemas/
          __init__.py
          common.py

      modules/
        __init__.py

        users/
          __init__.py
          models.py
          schemas.py
          repository.py
          service.py

        projects/
          __init__.py
          models.py
          schemas.py
          repository.py
          service.py

        responses/
          __init__.py
          models.py
          schemas.py
          repository.py
          service.py

        stats/
          __init__.py
          schemas.py
          service.py

    alembic/
      env.py
      script.py.mako
      versions/

    scripts/
      seed.py

    tests/

  frontend/
    README.md
    .env.example
    package.json
    tsconfig.json
    vite.config.ts

    src/
      app/
        main.tsx
        providers/
          AppProviders.tsx
        routes/
          AppRouter.tsx
        styles/
          globals.css

      pages/
        login/
          ui/LoginPage.tsx
        projects-list/
          ui/ProjectsListPage.tsx
        project-details/
          ui/ProjectDetailsPage.tsx
        admin-projects/
          ui/AdminProjectsPage.tsx
        admin-responses/
          ui/AdminResponsesPage.tsx
        admin-stats/
          ui/AdminStatsPage.tsx

      widgets/
        header/
          ui/Header.tsx
        project-card-list/
          ui/ProjectCardList.tsx
        project-details/
          ui/ProjectDetails.tsx
        admin-projects-table/
          ui/AdminProjectsTable.tsx
        admin-responses-table/
          ui/AdminResponsesTable.tsx

      features/
        auth-by-email/
          api/authApi.ts
          model/types.ts
          ui/LoginForm.tsx
        filter-projects/
          model/types.ts
          ui/ProjectFilters.tsx
        submit-project-response/
          api/submitProjectResponse.ts
          model/types.ts
          ui/ProjectResponseForm.tsx
        create-project/
          api/createProject.ts
          ui/CreateProjectForm.tsx
        edit-project/
          api/editProject.ts
          ui/EditProjectForm.tsx
        archive-project/
          api/archiveProject.ts
          ui/ArchiveProjectButton.tsx
        update-response-status/
          api/updateResponseStatus.ts
          ui/ResponseStatusSelect.tsx

      entities/
        project/
          api/projectApi.ts
          model/types.ts
          ui/ProjectCard.tsx
          ui/ProjectStatusBadge.tsx
          ui/ProjectPriorityBadge.tsx
        project-response/
          api/projectResponseApi.ts
          model/types.ts
          ui/ResponseStatusBadge.tsx
        user/
          api/userApi.ts
          model/types.ts

      shared/
        api/
          client.ts
        config/
          env.ts
        lib/
          date.ts
        ui/
          Badge.tsx
          Button.tsx
          Card.tsx
          EmptyState.tsx
          Input.tsx
          Modal.tsx
          PageLayout.tsx
          Select.tsx
          Spinner.tsx
          Table.tsx
          Textarea.tsx
```

## Root README должен содержать

```bash
docker compose up -d db

cd backend
cp .env.example .env
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload

cd ../frontend
cp .env.example .env
npm install
npm run dev
```

## Docker Compose

Минимально нужен PostgreSQL:

```yaml
services:
  db:
    image: postgres:17
    environment:
      POSTGRES_DB: project_showcase
      POSTGRES_USER: project_showcase
      POSTGRES_PASSWORD: project_showcase
    ports:
      - "5432:5432"
    volumes:
      - project_showcase_pg_data:/var/lib/postgresql/data

volumes:
  project_showcase_pg_data:
```
