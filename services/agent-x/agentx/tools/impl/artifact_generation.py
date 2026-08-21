"""Agent-X Artifact Generation Tool."""

import hashlib
from typing import Any

from agentx.tools.base import BaseTool
from agentx.tools.schemas import ToolDeclaration, ToolInvocationContext, ToolRiskLevel


class ArtifactGenerationTool(BaseTool):
    """Tool for compiling mission deliverables, generating evidence manifests, and SHA-256 proofs."""

    def __init__(self) -> None:
        super().__init__(
            declaration=ToolDeclaration(
                name="artifact_generation",
                description="Packages structured deliverables, markdown files, and generates SHA-256 checksums.",
                capabilities=["artifact_generation"],
                permissions=["artifact:export", "write:filesystem"],
                risk=ToolRiskLevel.LOW,
                estimated_cost=0.0004,
                timeout=10.0,
                input_schema={
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Target artifact filename"},
                        "content": {
                            "type": "string",
                            "description": "Text, markdown, or JSON string",
                        },
                        "content_type": {"type": "string", "default": "text/markdown"},
                    },
                    "required": ["filename", "content"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "sha256": {"type": "string"},
                        "size_bytes": {"type": "integer"},
                    },
                },
            )
        )

    async def _run(
        self, parameters: dict[str, Any], context: ToolInvocationContext
    ) -> dict[str, Any]:
        filename = str(parameters.get("filename", "deliverable.md"))
        raw_content = str(parameters.get("content", ""))
        content_type = str(parameters.get("content_type", "text/markdown"))

        content_bytes = raw_content.encode("utf-8")
        sha256_hash = hashlib.sha256(content_bytes).hexdigest()

        artifact_dict = {
            "filename": filename,
            "content_type": content_type,
            "size_bytes": len(content_bytes),
            "sha256": sha256_hash,
            "mission_id": context.mission_id,
            "task_id": context.task_id,
            "content_preview": raw_content[:200],
        }

        return {
            "filename": filename,
            "sha256": sha256_hash,
            "size_bytes": len(content_bytes),
            "content_type": content_type,
            "manifest_entry": artifact_dict,
            "__artifacts__": [artifact_dict],
        }
