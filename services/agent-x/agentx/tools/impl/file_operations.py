"""Agent-X Sandboxed File Operations Tool."""

import hashlib
from typing import Any

from agentx.tools.base import BaseTool
from agentx.tools.schemas import ToolDeclaration, ToolInvocationContext, ToolRiskLevel
from agentx.tools.security import sanitize_path, wrap_untrusted_content


class FileOperationsTool(BaseTool):
    """Tool for sandboxed filesystem manipulation with strict boundary checks."""

    def __init__(self) -> None:
        super().__init__(
            declaration=ToolDeclaration(
                name="file_operations",
                description="Performs sandboxed filesystem operations (read, write, list, patch, delete).",
                capabilities=["filesystem"],
                permissions=["read:filesystem", "write:filesystem"],
                risk=ToolRiskLevel.HIGH,
                estimated_cost=0.0005,
                timeout=10.0,
                input_schema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["read", "write", "list", "patch", "delete"],
                        },
                        "path": {"type": "string", "description": "Target file or directory path"},
                        "content": {"type": "string", "description": "Content for write action"},
                        "target_text": {
                            "type": "string",
                            "description": "Text to replace in patch action",
                        },
                        "replacement_text": {
                            "type": "string",
                            "description": "Replacement text for patch",
                        },
                    },
                    "required": ["action", "path"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string"},
                        "path": {"type": "string"},
                        "result": {"type": "object"},
                    },
                },
            )
        )

    async def _run(
        self, parameters: dict[str, Any], context: ToolInvocationContext
    ) -> dict[str, Any]:
        action = str(parameters.get("action", "")).lower()
        path_str = str(parameters.get("path", ""))

        target_path = sanitize_path(
            path_str=path_str,
            allowed_paths=context.allowed_paths,
            forbidden_paths=context.forbidden_paths,
        )

        if action == "read":
            if not target_path.exists() or not target_path.is_file():
                raise FileNotFoundError(f"File '{target_path}' does not exist")
            raw_content = target_path.read_text(encoding="utf-8")
            demarcated = wrap_untrusted_content(
                content=raw_content,
                source=f"file://{target_path}",
                metadata={"size_bytes": len(raw_content.encode("utf-8"))},
            )
            return {
                "action": "read",
                "path": str(target_path),
                "size_bytes": len(raw_content.encode("utf-8")),
                "content": demarcated,
                "__untrusted__": True,
            }

        elif action == "write":
            content = str(parameters.get("content", ""))
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            sha256_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            return {
                "action": "write",
                "path": str(target_path),
                "bytes_written": len(content.encode("utf-8")),
                "sha256": sha256_hash,
            }

        elif action == "list":
            if not target_path.exists() or not target_path.is_dir():
                raise NotADirectoryError(f"Directory '{target_path}' does not exist")
            entries: list[dict[str, Any]] = []
            for item in sorted(target_path.iterdir()):
                entries.append(
                    {
                        "name": item.name,
                        "is_dir": item.is_dir(),
                        "size_bytes": item.stat().st_size if item.is_file() else 0,
                    }
                )
            return {
                "action": "list",
                "path": str(target_path),
                "total_entries": len(entries),
                "entries": entries,
            }

        elif action == "patch":
            if not target_path.exists() or not target_path.is_file():
                raise FileNotFoundError(f"File '{target_path}' does not exist")
            target_text = str(parameters.get("target_text", ""))
            replacement_text = str(parameters.get("replacement_text", ""))
            existing_content = target_path.read_text(encoding="utf-8")
            if target_text not in existing_content:
                raise ValueError(f"Target text not found in '{target_path}'")
            new_content = existing_content.replace(target_text, replacement_text, 1)
            target_path.write_text(new_content, encoding="utf-8")
            return {
                "action": "patch",
                "path": str(target_path),
                "sha256": hashlib.sha256(new_content.encode("utf-8")).hexdigest(),
            }

        elif action == "delete":
            if target_path.exists() and target_path.is_file():
                target_path.unlink()
                return {"action": "delete", "path": str(target_path), "deleted": True}
            raise FileNotFoundError(f"File '{target_path}' does not exist for deletion")

        else:
            raise ValueError(f"Unsupported filesystem action: '{action}'")
