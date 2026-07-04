from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import Depends
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.agent_runtime import PluginManifest
from app.services.plugins import plugin_registry
from app.services.tools import tool_registry

router = APIRouter(tags=["extensions"])


class ToolCallRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


@router.get("/tools")
def list_tools() -> dict[str, list[str]]:
    return {"tools": tool_registry.list()}


@router.post("/tools/{tool_name}/call")
async def call_tool(tool_name: str, payload: ToolCallRequest) -> dict[str, Any]:
    try:
        return await tool_registry.call(tool_name, payload.arguments)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/plugins")
def list_plugins() -> dict[str, list[dict[str, Any]]]:
    return {"plugins": [plugin.__dict__ for plugin in plugin_registry.list()]}


@router.get("/plugin-manifests")
def list_plugin_manifests(
    organization_id: int | None = None,
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    statement = select(PluginManifest).order_by(PluginManifest.name)
    if organization_id is not None:
        statement = statement.where(
            (PluginManifest.organization_id == organization_id) | PluginManifest.organization_id.is_(None)
        )
    return {
        "plugins": [
            {
                "id": plugin.id,
                "organization_id": plugin.organization_id,
                "name": plugin.name,
                "version": plugin.version,
                "enabled": plugin.enabled,
                "capabilities": plugin.capabilities,
                "config_schema": plugin.config_schema,
            }
            for plugin in db.scalars(statement)
        ]
    }
