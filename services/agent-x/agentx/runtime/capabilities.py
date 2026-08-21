"""Agent-X Capability Registry for Managing and Querying Agent Skills."""

import threading

from agentx.runtime.schemas import Capability


class CapabilityRegistry:
    """Thread-safe registry for defining, querying, and verifying agent capabilities."""

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}
        self._agent_capability_map: dict[str, set[str]] = {}
        self._lock = threading.Lock()
        self._register_default_capabilities()

    def _register_default_capabilities(self) -> None:
        """Register the core standard capabilities of the Agent-X platform."""
        defaults = [
            Capability(
                name="planning",
                description="Deconstructs missions into structured task DAGs, identifies unknowns, and balances constraints.",
                required_tools=["world_model_query", "unknowns_calculator"],
            ),
            Capability(
                name="research",
                description="Queries information sources, gathers evidence, and attaches verifiable source provenance.",
                required_tools=["web_search", "knowledge_base", "file_reader"],
            ),
            Capability(
                name="analysis",
                description="Performs quantitative calculations, metric evaluations, risk scoring, and anomaly detection.",
                required_tools=["calculator", "data_formatter"],
            ),
            Capability(
                name="verification",
                description="Executes Level 1-4 Verification Protocol, artifact hashing, and cryptographic proof generation.",
                required_tools=["hasher", "schema_validator", "test_runner"],
            ),
            Capability(
                name="critique",
                description="Adversarial evaluation of deliverables, discovering edge cases, and catching hallucinations.",
                required_tools=["rule_checker", "diff_inspector"],
            ),
            Capability(
                name="recovery",
                description="Diagnoses task execution failures, performs RCA, and synthesizes dynamic self-healing DAG repairs.",
                required_tools=["error_classifier", "workflow_surgeon"],
            ),
            Capability(
                name="artifact_generation",
                description="Formats and packages formal reports, deliverables, code, and evidence bundles.",
                required_tools=["file_writer", "markdown_builder", "tar_packer"],
            ),
        ]
        for cap in defaults:
            self.register_capability(cap)

    def register_capability(self, capability: Capability) -> None:
        """Register a new capability in the registry."""
        with self._lock:
            self._capabilities[capability.name] = capability

    def get_capability(self, name: str) -> Capability | None:
        """Retrieve capability definition by name."""
        with self._lock:
            return self._capabilities.get(name)

    def list_capabilities(self) -> list[Capability]:
        """Return all registered capabilities."""
        with self._lock:
            return list(self._capabilities.values())

    def bind_capability_to_agent(self, agent_name: str, capability_name: str) -> None:
        """Bind a capability to a specific agent name or type."""
        with self._lock:
            if capability_name not in self._capabilities:
                raise ValueError(
                    f"Capability '{capability_name}' is not registered in CapabilityRegistry"
                )
            if agent_name not in self._agent_capability_map:
                self._agent_capability_map[agent_name] = set()
            self._agent_capability_map[agent_name].add(capability_name)

    def get_capabilities_for_agent(self, agent_name: str) -> list[Capability]:
        """Return all capabilities bound to a specific agent."""
        with self._lock:
            cap_names = self._agent_capability_map.get(agent_name, set())
            return [self._capabilities[name] for name in cap_names if name in self._capabilities]

    def find_agents_with_capability(self, capability_name: str) -> list[str]:
        """Find all agent names that possess the given capability."""
        with self._lock:
            return [
                agent
                for agent, caps in self._agent_capability_map.items()
                if capability_name in caps
            ]
