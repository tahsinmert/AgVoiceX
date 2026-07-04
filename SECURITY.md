# Security Policy

## Supported Versions

AgVoiceX is under active early development. Security fixes target the default branch unless a maintained release branch is explicitly announced.

## Reporting a Vulnerability

Please do not open a public issue for a suspected vulnerability.

Report security concerns through GitHub by contacting the repository owner or by using GitHub Security Advisories if they are enabled for the repository.

Include:

- Affected component or endpoint.
- Reproduction steps.
- Expected and actual behavior.
- Impact assessment.
- Any relevant logs with secrets removed.

## Security Expectations

- Do not commit `.env`, tokens, credentials, database dumps, or private knowledge data.
- Keep n8n basic auth enabled for shared environments.
- Put the admin UI and API behind authentication and TLS before internet exposure.
- Restrict CORS to trusted origins.
- Do not expose PostgreSQL, Redis, Qdrant, Ollama, or n8n directly to the public internet.

## Known Security Gaps

- First-party authentication and authorization are not implemented yet.
- Public API endpoints are intended for trusted local or protected network environments.
- Operator-controlled reverse proxy, VPN, or access gateway is required for production exposure.
