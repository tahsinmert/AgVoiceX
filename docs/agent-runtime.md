# Agent Runtime

The Agent Runtime is the internal orchestration layer behind `/api/v1/chat`.
It is local-first and keeps the existing FastAPI plus n8n architecture. It does
not add LangGraph, CrewAI, OpenAI Agents SDK, or any paid API dependency.

## Runtime Flow

1. Resolve tenant context from organization, business and agent ids.
2. Load the active agent, active prompt version, selected provider and selected model.
3. Load recent PostgreSQL-backed memory for the customer/context.
4. Ask the configured AI provider for a structured intent payload.
5. Build an execution plan with `InternalPlanner`.
6. Execute one approved domain tool through `ToolExecutor`.
7. Persist conversation history, compact memory and runtime events.

The public chat response remains backward compatible with the previous
`ConversationResponse` shape.

## Components

- `AgentRuntime`: coordinates planning, provider calls, tool execution and persistence.
- `InternalPlanner`: converts intent payloads into deterministic execution steps.
- `ToolExecutor`: executes reservation, knowledge, customer and admin tools.
- `MemoryManager`: stores compact conversation turns in `agent_memories`.
- `HybridRetrievalService`: searches knowledge rows and knowledge chunks with local PostgreSQL fallback.
- `EventBus`: writes operational events to `runtime_events`.
- `PluginSDK`: lets local plugins declare capabilities and register tool factories.

## Plugin SDK

Plugins are Python modules that register local tools. A minimal plugin looks like:

```python
from app.services.plugins import create_plugin, plugin_registry


class EchoTool:
    name = "demo.echo"

    async def call(self, arguments):
        return {"echo": arguments}


sdk = create_plugin("demo", capabilities=["tool:demo.echo"])
sdk.tool(EchoTool)
plugin_registry.register_sdk(sdk)
```

Tools should keep side effects explicit, validate arguments, and call existing
domain services instead of duplicating business rules.

## Runtime Tables

- `runtime_events`: append-only lifecycle and execution events.
- `agent_memories`: compact local memory scoped by organization, business, agent and customer.
- `plugin_manifests`: persistent plugin metadata for production operations.

## n8n Boundary

n8n remains an integration and workflow layer. Workflows should call backend
runtime, settings, model, reservation, knowledge and admin endpoints instead of
embedding AI provider details or model names.
