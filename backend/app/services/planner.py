from dataclasses import dataclass, field
from typing import Any

from app.schemas.intents import IntentPayload


@dataclass(frozen=True)
class RuntimePlanStep:
    name: str
    tool_name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimePlan:
    intent: IntentPayload
    steps: list[RuntimePlanStep]


class InternalPlanner:
    def plan(self, intent: IntentPayload) -> RuntimePlan:
        tool_map = {
            "reservation_create": "reservation.create",
            "reservation_update": "reservation.update",
            "reservation_cancel": "reservation.cancel",
            "reservation_lookup": "reservation.lookup",
            "faq": "knowledge.search",
            "customer_lookup": "customer.lookup",
            "admin_report": "admin.report",
        }
        steps = [RuntimePlanStep(name="load_context")]
        tool_name = tool_map.get(intent.intent)
        if tool_name:
            steps.append(RuntimePlanStep(name="execute_tool", tool_name=tool_name, arguments=intent.model_dump()))
        else:
            steps.append(RuntimePlanStep(name="respond"))
        return RuntimePlan(intent=intent, steps=steps)
