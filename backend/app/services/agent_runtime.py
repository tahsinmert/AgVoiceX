from sqlalchemy.orm import Session

from app.models.conversations import ConversationHistory
from app.schemas.conversations import ConversationRequest, ConversationResponse
from app.services.agents import AgentService
from app.services.ai_settings import AISettingsService
from app.services.event_bus import EventBus
from app.services.memory import MemoryManager
from app.services.planner import InternalPlanner
from app.services.tenancy import TenantService
from app.services.tool_executor import ToolExecutionResult, ToolExecutor


class AgentRuntime:
    def __init__(self, db: Session):
        self.db = db

    async def run(self, request: ConversationRequest) -> ConversationResponse:
        context = TenantService(self.db).resolve(request.organization_id, request.business_id, request.agent_id)
        agent_service = AgentService(self.db)
        agent = agent_service.load(context)
        if agent is not None and context.agent_id is None:
            context.agent_id = agent.id
        bus = EventBus(self.db, context)
        memory = MemoryManager(self.db, context)

        bus.publish("runtime.started", {"channel": request.channel})
        provider, model = await AISettingsService(self.db, context).resolve_for_agent(agent)
        prompt = agent_service.active_prompt_for(agent, "You are a local business AI agent.")
        intent = await provider.detect_intent(model, self._planner_input(prompt, request.message, request.metadata))
        plan = InternalPlanner().plan(intent)
        bus.publish(
            "planner.completed",
            {
                "intent": intent.intent,
                "steps": [step.__dict__ for step in plan.steps],
                "prompt_versioned": agent is not None,
            },
        )

        result = await self._execute_plan(plan, ToolExecutor(self.db, context))
        record = ConversationHistory(
            organization_id=context.organization_id,
            customer_id=result.customer_id or request.customer_id,
            channel=request.channel,
            user_message=request.message,
            intent=intent.intent,
            structured_output={
                "intent": intent.model_dump(),
                "plan": [step.__dict__ for step in plan.steps],
                "tool_result": dict(result),
            },
            assistant_reply=result.reply,
        )
        self.db.add(record)
        self.db.flush()
        memory.remember_turn(record)
        bus.publish("runtime.completed", {"intent": intent.intent}, conversation_id=record.id)
        self.db.commit()
        self.db.refresh(record)
        return ConversationResponse(
            reply=record.assistant_reply,
            intent=intent,
            conversation_id=record.id,
            customer_id=record.customer_id,
        )

    async def _execute_plan(self, plan, executor: ToolExecutor) -> ToolExecutionResult:
        for step in plan.steps:
            if step.tool_name:
                return await executor.execute(step.tool_name, step.arguments)
        return ToolExecutionResult(
            reply=plan.intent.reply
            or "I can help with reservations, customer lookups, FAQs, and admin reports. What would you like to do?"
        )

    @staticmethod
    def _planner_input(system_prompt: str, message: str, metadata: dict | None = None) -> str:
        context_lines = []
        reservation_type = (metadata or {}).get("reservation_type")
        if reservation_type:
            context_lines.append(f"Selected reservation category: {reservation_type}")
        scenario = (metadata or {}).get("scenario")
        if scenario:
            context_lines.append(f"Category operating guidance: {scenario}")

        sections = [system_prompt]
        if context_lines:
            sections.append("Conversation context:\n" + "\n".join(context_lines))
        sections.append(f"Current user message:\n{message}")
        return "\n\n".join(sections)
