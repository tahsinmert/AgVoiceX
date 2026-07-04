# Production Hardening Notes

This platform is local-first and self-hosted. Production operators should put it
behind a TLS-terminating reverse proxy and enforce authentication at the edge
until first-party auth is added.

## Security Boundaries

- Keep `.env` out of source control. Use `.env.example` only for defaults.
- Restrict `BACKEND_CORS_ORIGINS` to trusted admin and workflow origins.
- Do not expose PostgreSQL, Redis, Qdrant, Ollama or n8n directly on public networks.
- Change `N8N_BASIC_AUTH_PASSWORD` before shared demos or deployments.
- Use a reverse proxy or VPN for admin UI access.
- Knowledge ingestion is restricted to `ALLOWED_INGEST_ROOTS` and upload size is
  bounded by `MAX_UPLOAD_BYTES`.
- Browser voice mode uses browser APIs and the existing chat endpoint. It does
  not add telephony support.

## Operational Checks

```bash
python3 -m compileall backend/app
docker compose exec -T backend pytest tests
docker compose exec -T backend alembic upgrade head
cd frontend && npm audit --omit=dev && npm run build
docker compose config
bash scripts/dev-check.sh
```

## Known Gaps

- First-party authentication and authorization are not implemented yet.
- Tenant isolation is enforced in service-layer paths where tenant context is
  available, but public endpoints are still unauthenticated.
- Qdrant integration is prepared but PostgreSQL fallback search remains the
  default retrieval path.
