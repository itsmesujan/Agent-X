"""Agent-X Tool Subsystem Domain Schemas and Declarations."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolRiskLevel(StrEnum):
    """Risk categorization for tool operations."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ToolPermission(StrEnum):
    """Granular permission categories required by tools."""

    READ_FS = "read:filesystem"
    WRITE_FS = "write:filesystem"
    NET_READ = "network:read"
    COMPUTE_EVAL = "compute:eval"
    ARTIFACT_EXPORT = "artifact:export"


class ToolDeclaration(BaseModel):
    """Formal declaration and metadata for a tool in the registry."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Human and LLM readable tool purpose")
    capabilities: list[str] = Field(
        default_factory=list, description="Capabilities provided by this tool"
    )
    permissions: list[str] = Field(
        default_factory=list, description="System permissions required to execute"
    )
    risk: ToolRiskLevel = Field(default=ToolRiskLevel.LOW, description="Operational risk level")
    estimated_cost: float = Field(
        default=0.0001, ge=0.0, description="Estimated USD cost per invocation"
    )
    timeout: float = Field(default=30.0, gt=0.0, description="Execution timeout in seconds")
    input_schema: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for input parameters"
    )
    output_schema: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for structured outputs"
    )


class ToolInvocationContext(BaseModel):
    """Context and parameters dispatched to a tool for execution."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(..., description="Name of the tool being executed")
    mission_id: str = Field(..., description="Parent mission identifier")
    task_id: str | None = Field(default=None, description="Optional task identifier")
    agent_type: str | None = Field(default=None, description="Calling agent persona")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Validated parameter dictionary"
    )
    allowed_paths: list[str] = Field(
        default_factory=list, description="Filesystem paths permitted for access"
    )
    forbidden_paths: list[str] = Field(
        default_factory=list, description="Filesystem paths strictly denied"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ToolExecutionResult(BaseModel):
    """Result payload produced by tool execution."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(..., description="Name of the executed tool")
    is_success: bool = Field(..., description="Whether execution succeeded")
    data: dict[str, Any] = Field(default_factory=dict, description="Structured return payload")
    artifacts: list[dict[str, Any]] = Field(
        default_factory=list, description="Generated file artifacts or blobs"
    )
    untrusted_data_flag: bool = Field(
        default=False, description="Flag indicating content contains untrusted external data"
    )
    duration_ms: float = Field(
        default=0.0, ge=0.0, description="Execution duration in milliseconds"
    )
    cost_usd: float = Field(default=0.0, ge=0.0, description="Actual cost incurred")
    error_message: str | None = Field(
        default=None, description="Error message if is_success is False"
    )
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ToolExecutionError(Exception):
    """Base exception for tool execution errors."""

    def __init__(self, tool_name: str, message: str, details: str | None = None) -> None:
        self.tool_name = tool_name
        self.details = details
        super().__init__(f"Tool '{tool_name}' execution failed: {message}")


class ToolSecurityError(ToolExecutionError):
    """Raised on security violation (path traversal, prompt injection, forbidden action)."""

    pass


class ToolTimeoutError(ToolExecutionError):
    """Raised when tool execution exceeds declared timeout."""

    pass
