from typing import Any, Protocol


class Tool(Protocol):
    name: str

    async def call(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ...


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def list(self) -> list[str]:
        return sorted(self._tools)

    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return await self._tools[name].call(arguments)


tool_registry = ToolRegistry()
