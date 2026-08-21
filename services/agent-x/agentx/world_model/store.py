"""Agent-X World Model Store and Graph Traversal Interface."""

import threading
from abc import ABC, abstractmethod
from collections import deque
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentx.world_model.models import (
    Claim,
    Constraint,
    EntityType,
    Fact,
    Observation,
    RelationshipEdge,
    RelationshipType,
    Risk,
    SourceProvenance,
    Unknown,
    WorldModelEntity,
)
from agentx_common.schemas import EpistemicState


class ProvenanceTrace(BaseModel):
    """Immutable, verifiable audit trace linking a fact or claim to its root evidence."""

    model_config = ConfigDict(extra="forbid")

    target_id: str
    target_type: str  # "FACT" | "ENTITY" | "CLAIM" | "OBSERVATION"
    target_summary: str
    facts: list[Fact] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    sources: list[SourceProvenance] = Field(default_factory=list)
    evidence_uris: list[str] = Field(default_factory=list)
    evidence_hashes: list[str] = Field(default_factory=list)
    related_entity_ids: list[str] = Field(default_factory=list)
    chain_of_custody: list[dict[str, Any]] = Field(default_factory=list)
    traced_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WorldModelStore(ABC):
    """Abstract persistence interface for the World Model semantic graph."""

    @abstractmethod
    def save_entity(self, entity: WorldModelEntity) -> None:
        pass

    @abstractmethod
    def get_entity(self, mission_id: str, entity_id: str) -> WorldModelEntity | None:
        pass

    @abstractmethod
    def save_fact(self, fact: Fact) -> None:
        pass

    @abstractmethod
    def get_fact(self, mission_id: str, fact_id: str) -> Fact | None:
        pass

    @abstractmethod
    def save_claim(self, claim: Claim) -> None:
        pass

    @abstractmethod
    def get_claim(self, mission_id: str, claim_id: str) -> Claim | None:
        pass

    @abstractmethod
    def save_unknown(self, unknown: Unknown) -> None:
        pass

    @abstractmethod
    def get_unknown(self, mission_id: str, unknown_id: str) -> Unknown | None:
        pass

    @abstractmethod
    def save_constraint(self, constraint: Constraint) -> None:
        pass

    @abstractmethod
    def list_constraints(self, mission_id: str) -> list[Constraint]:
        pass

    @abstractmethod
    def save_risk(self, risk: Risk) -> None:
        pass

    @abstractmethod
    def list_risks(self, mission_id: str) -> list[Risk]:
        pass

    @abstractmethod
    def save_observation(self, observation: Observation) -> None:
        pass

    @abstractmethod
    def get_observation(self, mission_id: str, observation_id: str) -> Observation | None:
        pass

    @abstractmethod
    def save_edge(self, edge: RelationshipEdge) -> None:
        pass

    @abstractmethod
    def get_edges(
        self,
        mission_id: str,
        node_id: str | None = None,
        relationship: RelationshipType | None = None,
    ) -> list[RelationshipEdge]:
        pass

    @abstractmethod
    def query_entities(
        self,
        mission_id: str,
        entity_type: EntityType | None = None,
        epistemic_state: EpistemicState | None = None,
        min_confidence: float = 0.0,
    ) -> list[WorldModelEntity]:
        pass

    @abstractmethod
    def query_facts(
        self,
        mission_id: str,
        entity_id: str | None = None,
        subject: str | None = None,
        predicate: str | None = None,
        valid_only: bool = True,
    ) -> list[Fact]:
        pass

    @abstractmethod
    def trace_provenance(self, mission_id: str, target_id: str) -> ProvenanceTrace:
        pass


class InMemoryWorldModelStore(WorldModelStore):
    """Thread-safe in-memory semantic entity graph store with index support and provenance traversal."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entities: dict[tuple[str, str], WorldModelEntity] = {}
        self._facts: dict[tuple[str, str], Fact] = {}
        self._claims: dict[tuple[str, str], Claim] = {}
        self._unknowns: dict[tuple[str, str], Unknown] = {}
        self._constraints: dict[tuple[str, str], Constraint] = {}
        self._risks: dict[tuple[str, str], Risk] = {}
        self._observations: dict[tuple[str, str], Observation] = {}
        self._edges: dict[tuple[str, str], RelationshipEdge] = {}

    def save_entity(self, entity: WorldModelEntity) -> None:
        with self._lock:
            key = (entity.mission_id, entity.entity_id)
            self._entities[key] = entity.model_copy(deep=True)

    def get_entity(self, mission_id: str, entity_id: str) -> WorldModelEntity | None:
        with self._lock:
            key = (mission_id, entity_id)
            entity = self._entities.get(key)
            return entity.model_copy(deep=True) if entity else None

    def save_fact(self, fact: Fact) -> None:
        with self._lock:
            key = (fact.mission_id, fact.fact_id)
            self._facts[key] = fact.model_copy(deep=True)

    def get_fact(self, mission_id: str, fact_id: str) -> Fact | None:
        with self._lock:
            key = (mission_id, fact_id)
            fact = self._facts.get(key)
            return fact.model_copy(deep=True) if fact else None

    def save_claim(self, claim: Claim) -> None:
        with self._lock:
            key = (claim.mission_id, claim.claim_id)
            self._claims[key] = claim.model_copy(deep=True)

    def get_claim(self, mission_id: str, claim_id: str) -> Claim | None:
        with self._lock:
            key = (mission_id, claim_id)
            claim = self._claims.get(key)
            return claim.model_copy(deep=True) if claim else None

    def save_unknown(self, unknown: Unknown) -> None:
        with self._lock:
            key = (unknown.mission_id, unknown.unknown_id)
            self._unknowns[key] = unknown.model_copy(deep=True)

    def get_unknown(self, mission_id: str, unknown_id: str) -> Unknown | None:
        with self._lock:
            key = (mission_id, unknown_id)
            unk = self._unknowns.get(key)
            return unk.model_copy(deep=True) if unk else None

    def save_constraint(self, constraint: Constraint) -> None:
        with self._lock:
            key = (constraint.mission_id, constraint.constraint_id)
            self._constraints[key] = constraint.model_copy(deep=True)

    def list_constraints(self, mission_id: str) -> list[Constraint]:
        with self._lock:
            return [
                c.model_copy(deep=True)
                for (m_id, _), c in self._constraints.items()
                if m_id == mission_id
            ]

    def save_risk(self, risk: Risk) -> None:
        with self._lock:
            key = (risk.mission_id, risk.risk_id)
            self._risks[key] = risk.model_copy(deep=True)

    def list_risks(self, mission_id: str) -> list[Risk]:
        with self._lock:
            return [
                r.model_copy(deep=True)
                for (m_id, _), r in self._risks.items()
                if m_id == mission_id
            ]

    def save_observation(self, observation: Observation) -> None:
        with self._lock:
            key = (observation.mission_id, observation.observation_id)
            self._observations[key] = observation.model_copy(deep=True)

    def get_observation(self, mission_id: str, observation_id: str) -> Observation | None:
        with self._lock:
            key = (mission_id, observation_id)
            obs = self._observations.get(key)
            return obs.model_copy(deep=True) if obs else None

    def save_edge(self, edge: RelationshipEdge) -> None:
        with self._lock:
            key = (edge.mission_id, edge.edge_id)
            self._edges[key] = edge.model_copy(deep=True)

    def get_edges(
        self,
        mission_id: str,
        node_id: str | None = None,
        relationship: RelationshipType | None = None,
    ) -> list[RelationshipEdge]:
        with self._lock:
            results: list[RelationshipEdge] = []
            for (m_id, _), edge in self._edges.items():
                if m_id != mission_id:
                    continue
                if node_id and (edge.source_id != node_id and edge.target_id != node_id):
                    continue
                if relationship and edge.relationship != relationship:
                    continue
                results.append(edge.model_copy(deep=True))
            return results

    def query_entities(
        self,
        mission_id: str,
        entity_type: EntityType | None = None,
        epistemic_state: EpistemicState | None = None,
        min_confidence: float = 0.0,
    ) -> list[WorldModelEntity]:
        with self._lock:
            results: list[WorldModelEntity] = []
            for (m_id, _), ent in self._entities.items():
                if m_id != mission_id:
                    continue
                if entity_type and ent.entity_type != entity_type:
                    continue
                if epistemic_state and ent.epistemic_state != epistemic_state:
                    continue
                if ent.confidence < min_confidence:
                    continue
                results.append(ent.model_copy(deep=True))
            return results

    def query_facts(
        self,
        mission_id: str,
        entity_id: str | None = None,
        subject: str | None = None,
        predicate: str | None = None,
        valid_only: bool = True,
    ) -> list[Fact]:
        with self._lock:
            results: list[Fact] = []
            for (m_id, _), fact in self._facts.items():
                if m_id != mission_id:
                    continue
                if entity_id and fact.entity_id != entity_id:
                    continue
                if subject and subject.lower() not in fact.subject.lower():
                    continue
                if predicate and predicate.lower() != fact.predicate.lower():
                    continue
                if valid_only and not fact.is_valid:
                    continue
                results.append(fact.model_copy(deep=True))
            return results

    def trace_provenance(self, mission_id: str, target_id: str) -> ProvenanceTrace:
        """Trace backward through observations, generating tasks, sources, and GCS URIs."""
        with self._lock:
            visited_nodes: set[str] = set()
            queue: deque[str] = deque([target_id])

            facts_collected: list[Fact] = []
            obs_collected: list[Observation] = []
            sources_collected: list[SourceProvenance] = []
            evidence_uris: set[str] = set()
            evidence_hashes: set[str] = set()
            related_entity_ids: set[str] = set()
            chain_of_custody: list[dict[str, Any]] = []

            target_type = "UNKNOWN"
            target_summary = f"Node {target_id}"

            # Check if root is Fact, Entity, Claim, or Observation
            initial_fact = self._facts.get((mission_id, target_id))
            initial_entity = self._entities.get((mission_id, target_id))
            initial_claim = self._claims.get((mission_id, target_id))
            initial_obs = self._observations.get((mission_id, target_id))

            if initial_fact:
                target_type = "FACT"
                target_summary = (
                    f"Fact: {initial_fact.subject} {initial_fact.predicate} = {initial_fact.value}"
                )
            elif initial_entity:
                target_type = "ENTITY"
                target_summary = f"Entity: {initial_entity.entity_type} {initial_entity.name}"
            elif initial_claim:
                target_type = "CLAIM"
                target_summary = f"Claim: {initial_claim.statement}"
            elif initial_obs:
                target_type = "OBSERVATION"
                target_summary = f"Observation: {initial_obs.summary}"

            while queue:
                current_id = queue.popleft()
                if current_id in visited_nodes:
                    continue
                visited_nodes.add(current_id)

                # 1. Check Fact
                fact = self._facts.get((mission_id, current_id))
                if fact:
                    facts_collected.append(fact)
                    sources_collected.append(fact.source)
                    if fact.source.evidence_uri:
                        evidence_uris.add(fact.source.evidence_uri)
                    if fact.source.raw_evidence_hash:
                        evidence_hashes.add(fact.source.raw_evidence_hash)
                    if fact.entity_id:
                        related_entity_ids.add(fact.entity_id)

                    chain_of_custody.append(
                        {
                            "node_id": fact.fact_id,
                            "type": "FACT",
                            "subject": fact.subject,
                            "predicate": fact.predicate,
                            "source_type": fact.source.source_type.value,
                            "source_ref": fact.source.source_ref,
                            "task_id": fact.source.task_id,
                            "timestamp": fact.created_at.isoformat(),
                        }
                    )

                    for obs_id in fact.observation_ids:
                        queue.append(obs_id)

                # 2. Check Observation
                obs = self._observations.get((mission_id, current_id))
                if obs:
                    obs_collected.append(obs)
                    sources_collected.append(obs.source)
                    if obs.source.evidence_uri:
                        evidence_uris.add(obs.source.evidence_uri)
                    if obs.source.raw_evidence_hash:
                        evidence_hashes.add(obs.source.raw_evidence_hash)

                    chain_of_custody.append(
                        {
                            "node_id": obs.observation_id,
                            "type": "OBSERVATION",
                            "summary": obs.summary,
                            "source_type": obs.source.source_type.value,
                            "source_ref": obs.source.source_ref,
                            "task_id": obs.source.task_id,
                            "timestamp": obs.timestamp.isoformat(),
                        }
                    )

                # 3. Check Entity
                ent = self._entities.get((mission_id, current_id))
                if ent:
                    related_entity_ids.add(ent.entity_id)
                    if ent.evidence_uri:
                        evidence_uris.add(ent.evidence_uri)
                    if ent.source:
                        sources_collected.append(ent.source)

                # 4. Check Claim
                clm = self._claims.get((mission_id, current_id))
                if clm:
                    for uri in clm.supporting_evidence_uris:
                        evidence_uris.add(uri)
                    if clm.entity_id:
                        related_entity_ids.add(clm.entity_id)

                # 5. Traverse incoming edges (DERIVED_FROM, OBSERVED_FROM, SUPERSEDES)
                for (m_id, _), edge in self._edges.items():
                    if m_id == mission_id and edge.target_id == current_id:
                        queue.append(edge.source_id)

            return ProvenanceTrace(
                target_id=target_id,
                target_type=target_type,
                target_summary=target_summary,
                facts=facts_collected,
                observations=obs_collected,
                sources=sources_collected,
                evidence_uris=sorted(evidence_uris),
                evidence_hashes=sorted(evidence_hashes),
                related_entity_ids=sorted(related_entity_ids),
                chain_of_custody=chain_of_custody,
            )

    def clear(self) -> None:
        """Clear all store contents."""
        with self._lock:
            self._entities.clear()
            self._facts.clear()
            self._claims.clear()
            self._unknowns.clear()
            self._constraints.clear()
            self._risks.clear()
            self._observations.clear()
            self._edges.clear()
