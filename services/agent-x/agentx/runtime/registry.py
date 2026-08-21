"""Agent-X Agent Registry for Managing, Discovering, and Dispatching Agents."""

import threading

from agentx.runtime.base import BaseAgent
from agentx.runtime.capabilities import CapabilityRegistry
from agentx.runtime.schemas import AgentType


class AgentNotFoundError(Exception):
    """Raised when an agent cannot be found in the registry."""

    def __init__(self, identifier: str) -> None:
        super().__init__(f"Agent with identifier '{identifier}' was not found in AgentRegistry")


class AgentRegistry:
    """Thread-safe registry for managing, discovering, and dispatching specialized agents."""

    def __init__(self, capability_registry: CapabilityRegistry | None = None) -> None:
        self._agents: dict[str, BaseAgent] = {}
        self.capability_registry = capability_registry or CapabilityRegistry()
        self._lock = threading.Lock()

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent instance and bind its capabilities."""
        key = agent.agent_type.value
        with self._lock:
            self._agents[key] = agent
            self._agents[agent.name] = agent

            # Bind capabilities in capability registry
            for cap in agent.capabilities:
                try:
                    self.capability_registry.bind_capability_to_agent(agent.name, cap)
                    self.capability_registry.bind_capability_to_agent(key, cap)
                except ValueError:
                    # Non-fatal if capability was custom and not yet registered
                    pass

    def get_agent(self, identifier: AgentType | str) -> BaseAgent:
        """Retrieve an agent by AgentType or string name."""
        key = identifier.value if isinstance(identifier, AgentType) else str(identifier)
        with self._lock:
            if key not in self._agents:
                raise AgentNotFoundError(key)
            return self._agents[key]

    def has_agent(self, identifier: AgentType | str) -> bool:
        """Check if an agent is registered."""
        key = identifier.value if isinstance(identifier, AgentType) else str(identifier)
        with self._lock:
            return key in self._agents

    def list_agents(self) -> list[BaseAgent]:
        """Return unique list of all registered agents."""
        with self._lock:
            # Filter unique by id to avoid duplicates between name and type keys
            seen_ids: set[int] = set()
            unique_agents: list[BaseAgent] = []
            for a in self._agents.values():
                if id(a) not in seen_ids:
                    seen_ids.add(id(a))
                    unique_agents.append(a)
            return unique_agents

    def find_agents_by_capability(self, capability_name: str) -> list[BaseAgent]:
        """Find all registered agents that support a specific capability."""
        agent_names = self.capability_registry.find_agents_with_capability(capability_name)
        result: list[BaseAgent] = []
        with self._lock:
            for name in agent_names:
                if name in self._agents:
                    agent = self._agents[name]
                    if agent not in result:
                        result.append(agent)
        return result

    def unregister_agent(self, identifier: AgentType | str) -> BaseAgent | None:
        """Remove an agent from the registry."""
        key = identifier.value if isinstance(identifier, AgentType) else str(identifier)
        with self._lock:
            agent = self._agents.pop(key, None)
            if agent:
                self._agents.pop(agent.name, None)
                self._agents.pop(agent.agent_type.value, None)
            return agent
