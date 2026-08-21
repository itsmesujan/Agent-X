"""Agent-X Artifact Agent."""

import hashlib
from typing import Any

from agentx.runtime.base import BaseAgent
from agentx.runtime.schemas import AgentInvocationContext, AgentType


class ArtifactAgent(BaseAgent):
    """Specialized agent for deliverable assembly, markdown compilation, and evidence bundling."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            agent_type=AgentType.ARTIFACT,
            name="ArtifactAgent",
            description="Compiles structured mission deliverables, reports, and cryptographic artifact manifests.",
            capabilities=["artifact_generation"],
            **kwargs,
        )

    async def _execute_internal(self, context: AgentInvocationContext) -> dict[str, Any]:
        """Assembles structured deliverables and packages files with cryptographic hashes."""
        title = context.inputs.get("title", f"Deliverable for {context.mission_id}")
        sections = context.inputs.get("sections", {})
        raw_content = context.inputs.get("raw_content", "")

        # Format markdown document
        md_lines = [f"# {title}\n", f"**Mission ID**: `{context.mission_id}`\n"]
        if isinstance(sections, dict):
            for heading, content in sections.items():
                md_lines.append(f"## {heading}\n\n{content}\n")
        elif raw_content:
            md_lines.append(str(raw_content))

        compiled_markdown = "\n".join(md_lines)
        file_bytes = compiled_markdown.encode("utf-8")
        file_sha256 = hashlib.sha256(file_bytes).hexdigest()

        artifact_metadata = {
            "filename": context.inputs.get("filename", "mission_deliverable.md"),
            "content_type": "text/markdown",
            "size_bytes": len(file_bytes),
            "sha256": file_sha256,
            "content_snippet": compiled_markdown[:200],
        }

        return {
            "title": title,
            "artifact_count": 1,
            "primary_artifact_sha256": file_sha256,
            "manifest": [artifact_metadata],
            "__artifacts__": [artifact_metadata],
            "__confidence__": 1.0,
            "__tokens_used__": 2000,
            "__cost_usd__": 0.0006,
        }
