from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.services.tools import Tool, tool_registry


@dataclass
class Plugin:
    name: str
    enabled: bool = True
    capabilities: list[str] = field(default_factory=list)
    version: str = "0.1.0"
    config_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginSDK:
    plugin: Plugin
    tool_factories: list[Callable[[], Tool]] = field(default_factory=list)

    def tool(self, factory: Callable[[], Tool]) -> Callable[[], Tool]:
        self.tool_factories.append(factory)
        return factory


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        self._plugins[plugin.name] = plugin

    def list(self) -> list[Plugin]:
        return sorted(self._plugins.values(), key=lambda plugin: plugin.name)

    def register_sdk(self, sdk: PluginSDK) -> None:
        self.register(sdk.plugin)
        if not sdk.plugin.enabled:
            return
        for factory in sdk.tool_factories:
            tool_registry.register(factory())


def create_plugin(
    name: str,
    capabilities: list[str] | None = None,
    version: str = "0.1.0",
    enabled: bool = True,
    config_schema: dict[str, Any] | None = None,
) -> PluginSDK:
    return PluginSDK(
        plugin=Plugin(
            name=name,
            version=version,
            enabled=enabled,
            capabilities=capabilities or [],
            config_schema=config_schema or {},
        )
    )


plugin_registry = PluginRegistry()
