"""Agent-X Document Reader Tool."""

from typing import Any

from agentx.tools.base import BaseTool
from agentx.tools.schemas import ToolDeclaration, ToolInvocationContext, ToolRiskLevel
from agentx.tools.security import sanitize_path, wrap_untrusted_content


class DocumentReaderTool(BaseTool):
    """Tool for reading and parsing structured documents and files with untrusted wrapping."""

    def __init__(self) -> None:
        super().__init__(
            declaration=ToolDeclaration(
                name="document_reader",
                description="Reads documents and extracts structured text while isolating untrusted content.",
                capabilities=["research", "analysis"],
                permissions=["read:filesystem"],
                risk=ToolRiskLevel.LOW,
                estimated_cost=0.0002,
                timeout=10.0,
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Filesystem path to read"},
                        "content": {
                            "type": "string",
                            "description": "Direct text content if no file path",
                        },
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "char_count": {"type": "integer"},
                        "demarcated_content": {"type": "string"},
                    },
                },
            )
        )

    async def _run(
        self, parameters: dict[str, Any], context: ToolInvocationContext
    ) -> dict[str, Any]:
        path_str = parameters.get("path")
        direct_content = parameters.get("content")

        if path_str:
            target_path = sanitize_path(
                path_str=path_str,
                allowed_paths=context.allowed_paths,
                forbidden_paths=context.forbidden_paths,
            )
            if not target_path.exists() or not target_path.is_file():
                raise FileNotFoundError(f"Document '{target_path}' not found")
            raw_text = target_path.read_text(encoding="utf-8")
            source_name = str(target_path)
        elif direct_content is not None:
            raw_text = str(direct_content)
            source_name = "inline_document"
        else:
            raise ValueError("Must provide either 'path' or 'content'")

        demarcated_content = wrap_untrusted_content(
            content=raw_text,
            source=source_name,
            metadata={"size_chars": len(raw_text)},
        )

        return {
            "source": source_name,
            "char_count": len(raw_text),
            "line_count": len(raw_text.splitlines()),
            "demarcated_content": demarcated_content,
            "__untrusted__": True,
        }
