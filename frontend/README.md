# Frontend

React + TypeScript frontend для MVP «Витрина проектов ШПИУ».

## Запуск

```bash
cp .env.example .env
npm install
npm run dev
```

Приложение будет доступно на `http://localhost:5173`.

## Проверки

```bash
npm test
npm run build
```

E2E-тесты требуют запущенные backend на `http://localhost:8000` и frontend на `http://localhost:5173`:

```bash
npm run test:e2e
```
