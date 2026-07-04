# Multi-Tenant Agent Platform

Phase 3 adds tenant and agent boundaries without replacing the original text-conversation flow.

## Tenant Model

- `organizations` own all platform resources.
- `businesses` belong to one organization.
- `agents` belong to an organization and can optionally belong to a business.
- `prompts` belong to an organization and can optionally version prompts per agent.
- Existing resources now carry `organization_id` while legacy endpoints continue to use a default organization.

## Backward Compatibility

If a request does not pass `organization_id`, the backend creates and uses:

- organization slug: `default`
- business slug: `default`

This keeps `/api/v1/chat`, reservations, customers, settings, and knowledge usable for single-tenant installs.

## Agent Loading

Conversation requests can include:

```json
{
  "message": "Hello",
  "organization_id": 1,
  "business_id": 1,
  "agent_id": 1
}
```

The backend resolves the tenant, loads the active agent, applies the agent provider/model when present, and falls back to organization-level provider/model settings.

## Provider And Model Management

Provider and model settings are stored in `business_settings` per organization:

- `ai.provider`
- `ai.model`

Use:

- `GET /api/v1/providers?organization_id=1`
- `GET /api/v1/models?organization_id=1`
- `PUT /api/v1/settings/provider`
- `PUT /api/v1/settings/model`

## Streaming

`POST /api/v1/chat/stream` streams text from the active provider using the selected tenant/agent context.

## Tools And Plugins

Tool and plugin registries are isolated in:

- `app.services.tools`
- `app.services.plugins`

They expose:

- `GET /api/v1/tools`
- `POST /api/v1/tools/{tool_name}/call`
- `GET /api/v1/plugins`

These registries are intentionally small extension points. Concrete tools and plugins should register themselves without coupling provider, conversation, or persistence code.
