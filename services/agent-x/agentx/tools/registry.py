"""Agent-X Tool Registry for Registering, Discovering, and Executing Tools."""

import threading

from agentx.kernel.events import EventBus, EventType, ToolExecutionEvent
from agentx.tools.base import BaseTool
from agentx.tools.impl import (
    ArtifactGenerationTool,
    CalculatorTool,
    DataAnalysisTool,
    DocumentReaderTool,
    FileOperationsTool,
    WebResearchTool,
)
from agentx.tools.schemas import (
    ToolDeclaration,
    ToolExecutionResult,
    ToolInvocationContext,
)


class ToolNotFoundError(Exception):
    """Raised when a requested tool is not found in the registry."""

    def __init__(self, tool_name: str) -> None:
        super().__init__(f"Tool with name '{tool_name}' was not found in ToolRegistry")


class ToolRegistry:
    """Thread-safe registry for managing and dispatching tools, enforcing policies, and emitting events."""

    def __init__(
        self,
        event_bus: EventBus | None = None,
        auto_register_defaults: bool = True,
    ) -> None:
        self._tools: dict[str, BaseTool] = {}
        self.event_bus = event_bus or EventBus()
        self._lock = threading.Lock()

        if auto_register_defaults:
            self._register_defaults()

    def _register_defaults(self) -> None:
        """Register the 6 core standard tools."""
        defaults: list[BaseTool] = [
            WebResearchTool(),
            DocumentReaderTool(),
            DataAnalysisTool(),
            CalculatorTool(),
            FileOperationsTool(),
            ArtifactGenerationTool(),
        ]
        for tool in defaults:
            self.register_tool(tool)

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool instance in the registry."""
        with self._lock:
            self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        """Retrieve a registered tool by name."""
        with self._lock:
            if name not in self._tools:
                raise ToolNotFoundError(name)
            return self._tools[name]

    def has_tool(self, name: str) -> bool:
        """Check if a tool exists in the registry."""
        with self._lock:
            return name in self._tools

    def list_tools(self) -> list[ToolDeclaration]:
        """Return all declared tool specifications."""
        with self._lock:
            return [tool.declaration for tool in self._tools.values()]

    def list_tool_instances(self) -> list[BaseTool]:
        """Return all registered tool instances."""
        with self._lock:
            return list(self._tools.values())

    def find_tools_by_capability(self, capability: str) -> list[BaseTool]:
        """Find all tools that support a specific capability."""
        with self._lock:
            return [t for t in self._tools.values() if capability in t.declaration.capabilities]

    def find_tools_by_permission(self, permission: str) -> list[BaseTool]:
        """Find all tools requiring a specific permission."""
        with self._lock:
            return [t for t in self._tools.values() if permission in t.declaration.permissions]

    async def invoke_tool(self, context: ToolInvocationContext) -> ToolExecutionResult:
        """Executes a registered tool and publishes a ToolExecutionEvent on the EventBus."""
        tool = self.get_tool(context.tool_name)
        result = await tool.execute(context)

        # Emit mandatory ToolExecutionEvent on every invocation
        evt_type = EventType.TOOL_INVOKED if result.is_success else EventType.TOOL_FAILED
        status_str = (
            "SUCCESS"
            if result.is_success
            else (
                "SECURITY_DENIED" if "SECURITY_DENIED" in (result.error_message or "") else "FAILED"
            )
        )

        event = ToolExecutionEvent(
            mission_id=context.mission_id,
            event_type=evt_type,
            tool_name=tool.name,
            task_id=context.task_id,
            agent_type=context.agent_type,
            status=status_str,
            risk_level=tool.declaration.risk.value,
            duration_ms=result.duration_ms,
            cost_usd=result.cost_usd,
            error_message=result.error_message,
            payload={
                "is_success": result.is_success,
                "untrusted_data_flag": result.untrusted_data_flag,
                "artifacts_count": len(result.artifacts),
            },
        )
        self.event_bus.publish(event)
        return result
