# Contributing to AgVoiceX

Thank you for helping improve AgVoiceX. This project aims to stay practical, local-first, and honest about what is implemented.

## Development Principles

- Prefer real integrations over placeholders.
- Keep tenant boundaries explicit.
- Keep domain rules in backend services, not duplicated in n8n workflows or UI code.
- Add tests for behavior that affects reservations, runtime execution, provider selection, or persistence.
- Document operational tradeoffs when a change affects deployment, security, or local model requirements.

## Local Setup

```bash
cp .env.example .env
docker compose up -d
docker compose exec backend alembic upgrade head
```

Backend:

```bash
cd backend
python3.10 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest -q
ruff check app tests
```

Frontend:

```bash
cd frontend
npm install
npm run build
```

## Pull Request Checklist

- The change is scoped and described clearly.
- Backend tests pass when backend behavior changes.
- Frontend build passes when UI or TypeScript changes.
- Migrations are included for schema changes.
- README or docs are updated for user-facing behavior.
- No secrets, `.env` files, generated caches, or local knowledge data are committed.

## Commit Style

Use concise, imperative commit messages:

```text
Improve voice runtime orchestration
Add reservation conflict tests
Document local model setup
```
