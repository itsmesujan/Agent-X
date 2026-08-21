"""Agent-X World Model Service."""

from datetime import UTC, datetime
from typing import Any

from agentx.world_model.models import (
    Claim,
    Constraint,
    Fact,
    Observation,
    RelationshipEdge,
    RelationshipType,
    Risk,
    Unknown,
    WorldModelEntity,
)
from agentx.world_model.store import InMemoryWorldModelStore, ProvenanceTrace, WorldModelStore
from agentx_common.schemas import EpistemicState


class EntityNotFoundError(Exception):
    """Raised when an entity is not found in the world model."""

    pass


class FactNotFoundError(Exception):
    """Raised when a fact is not found in the world model."""

    pass


class UnknownNotFoundError(Exception):
    """Raised when an unknown is not found in the world model."""

    pass


class WorldModel:
    """Manages the semantic entity graph, epistemic transitions, fact invalidation, and provenance tracing."""

    def __init__(self, mission_id: str, store: WorldModelStore | None = None) -> None:
        self.mission_id = mission_id
        self.store: WorldModelStore = store or InMemoryWorldModelStore()

    # --- 1. CREATE ---

    def register_entity(self, entity: WorldModelEntity) -> WorldModelEntity:
        """Register a new semantic entity in the world model."""
        if entity.mission_id != self.mission_id:
            raise ValueError(
                f"Entity mission_id '{entity.mission_id}' does not match WorldModel mission_id '{self.mission_id}'"
            )
        self.store.save_entity(entity)
        return entity

    def record_observation(self, observation: Observation) -> Observation:
        """Record an empirical observation with source provenance."""
        if observation.mission_id != self.mission_id:
            raise ValueError(
                f"Observation mission_id '{observation.mission_id}' does not match WorldModel '{self.mission_id}'"
            )
        self.store.save_observation(observation)
        return observation

    def assert_fact(self, fact: Fact) -> Fact:
        """Assert a verified or inferred fact, maintaining bidirectional links to observations."""
        if fact.mission_id != self.mission_id:
            raise ValueError(
                f"Fact mission_id '{fact.mission_id}' does not match WorldModel '{self.mission_id}'"
            )
        self.store.save_fact(fact)

        # Automatically create DERIVED_FROM edges between Fact and Observations
        for obs_id in fact.observation_ids:
            edge = RelationshipEdge(
                mission_id=self.mission_id,
                source_id=obs_id,
                target_id=fact.fact_id,
                relationship=RelationshipType.DERIVED_FROM,
                metadata={"asserted_at": datetime.now(UTC).isoformat()},
            )
            self.store.save_edge(edge)

        return fact

    def make_claim(self, claim: Claim) -> Claim:
        """Register a working hypothesis or assumption formulated by a subagent."""
        if claim.mission_id != self.mission_id:
            raise ValueError("Claim mission_id mismatch")
        self.store.save_claim(claim)
        return claim

    def register_unknown(self, unknown: Unknown) -> Unknown:
        """Register an epistemic gap or missing information requiring discovery."""
        if unknown.mission_id != self.mission_id:
            raise ValueError("Unknown mission_id mismatch")
        self.store.save_unknown(unknown)
        return unknown

    def register_constraint(self, constraint: Constraint) -> Constraint:
        """Register an operational or architectural constraint."""
        if constraint.mission_id != self.mission_id:
            raise ValueError("Constraint mission_id mismatch")
        self.store.save_constraint(constraint)
        return constraint

    def register_risk(self, risk: Risk) -> Risk:
        """Register an identified risk in the environment."""
        if risk.mission_id != self.mission_id:
            raise ValueError("Risk mission_id mismatch")
        self.store.save_risk(risk)
        return risk

    def link_nodes(
        self,
        source_id: str,
        target_id: str,
        relationship: RelationshipType,
        metadata: dict[str, Any] | None = None,
    ) -> RelationshipEdge:
        """Establish a semantic directed relationship between two nodes in the graph."""
        edge = RelationshipEdge(
            mission_id=self.mission_id,
            source_id=source_id,
            target_id=target_id,
            relationship=relationship,
            metadata=metadata or {},
        )
        self.store.save_edge(edge)
        return edge

    # --- 2. UPDATE ---

    def update_entity_properties(
        self,
        entity_id: str,
        properties: dict[str, Any],
        confidence: float | None = None,
        epistemic_state: EpistemicState | None = None,
        evidence_uri: str | None = None,
    ) -> WorldModelEntity:
        """Update properties and epistemic verification state of an entity."""
        entity = self.store.get_entity(self.mission_id, entity_id)
        if not entity:
            raise EntityNotFoundError(
                f"Entity '{entity_id}' not found in mission '{self.mission_id}'"
            )

        entity.properties.update(properties)
        if confidence is not None:
            entity.confidence = confidence
        if epistemic_state is not None:
            entity.epistemic_state = epistemic_state
        if evidence_uri is not None:
            entity.evidence_uri = evidence_uri
        entity.updated_at = datetime.now(UTC)

        self.store.save_entity(entity)
        return entity

    def resolve_unknown(self, unknown_id: str, resolved_fact_id: str) -> Unknown:
        """Atomically transition a CRITICAL_UNKNOWN into a resolved state linked to a verified Fact."""
        unknown = self.store.get_unknown(self.mission_id, unknown_id)
        if not unknown:
            raise UnknownNotFoundError(f"Unknown '{unknown_id}' not found")

        fact = self.store.get_fact(self.mission_id, resolved_fact_id)
        if not fact:
            raise FactNotFoundError(f"Resolved fact '{resolved_fact_id}' not found")

        now = datetime.now(UTC)
        unknown.is_resolved = True
        unknown.resolved_fact_id = resolved_fact_id
        unknown.resolved_at = now

        self.store.save_unknown(unknown)

        # Link Unknown to Fact
        self.link_nodes(
            source_id=resolved_fact_id,
            target_id=unknown_id,
            relationship=RelationshipType.VERIFIES,
            metadata={"resolved_at": now.isoformat()},
        )
        return unknown

    # --- 3. INVALIDATE ---

    def invalidate_fact(self, fact_id: str, reason: str) -> Fact:
        """Mark a fact as invalidated/refuted and record the reason."""
        fact = self.store.get_fact(self.mission_id, fact_id)
        if not fact:
            raise FactNotFoundError(f"Fact '{fact_id}' not found")

        now = datetime.now(UTC)
        fact.is_valid = False
        fact.invalidated_at = now
        fact.invalidated_reason = reason
        fact.updated_at = now

        self.store.save_fact(fact)
        return fact

    # --- 4. SUPERSEDE ---

    def supersede_fact(
        self,
        old_fact_id: str,
        new_fact: Fact,
        reason: str = "Superseded by newer observation",
    ) -> tuple[Fact, Fact, RelationshipEdge]:
        """Mark an existing fact as superseded by a newer fact and record a SUPERSEDES edge."""
        old_fact = self.store.get_fact(self.mission_id, old_fact_id)
        if not old_fact:
            raise FactNotFoundError(f"Old fact '{old_fact_id}' not found to supersede")

        # 1. Assert new fact
        self.assert_fact(new_fact)

        # 2. Invalidate old fact and point to new fact
        now = datetime.now(UTC)
        old_fact.is_valid = False
        old_fact.invalidated_at = now
        old_fact.invalidated_reason = f"Superseded by '{new_fact.fact_id}': {reason}"
        old_fact.superseded_by_fact_id = new_fact.fact_id
        old_fact.updated_at = now
        self.store.save_fact(old_fact)

        # 3. Create SUPERSEDES relationship edge
        edge = self.link_nodes(
            source_id=new_fact.fact_id,
            target_id=old_fact_id,
            relationship=RelationshipType.SUPERSEDES,
            metadata={"reason": reason, "timestamp": now.isoformat()},
        )

        return old_fact, new_fact, edge

    # --- 5. QUERY ---

    def get_entity(self, entity_id: str) -> WorldModelEntity | None:
        return self.store.get_entity(self.mission_id, entity_id)

    def get_fact(self, fact_id: str) -> Fact | None:
        return self.store.get_fact(self.mission_id, fact_id)

    def get_active_facts(
        self, entity_id: str | None = None, subject: str | None = None
    ) -> list[Fact]:
        return self.store.query_facts(
            mission_id=self.mission_id,
            entity_id=entity_id,
            subject=subject,
            valid_only=True,
        )

    def get_unresolved_unknowns(self) -> list[Unknown]:
        store = self.store
        if isinstance(store, InMemoryWorldModelStore):
            return [
                unk.model_copy(deep=True)
                for (m_id, _), unk in store._unknowns.items()
                if m_id == self.mission_id and not unk.is_resolved
            ]
        return []

    def get_active_risks(self) -> list[Risk]:
        return [r for r in self.store.list_risks(self.mission_id) if not r.is_mitigated]

    def get_constraints(self) -> list[Constraint]:
        return self.store.list_constraints(self.mission_id)

    def get_environment_snapshot(self) -> dict[str, Any]:
        """Aggregate high-level overview of the entire operating environment state."""
        entities = self.store.query_entities(self.mission_id)
        facts = self.get_active_facts()
        unknowns = self.get_unresolved_unknowns()
        risks = self.get_active_risks()
        constraints = self.get_constraints()

        return {
            "mission_id": self.mission_id,
            "entity_count": len(entities),
            "verified_facts_count": len(facts),
            "unresolved_unknowns_count": len(unknowns),
            "active_risks_count": len(risks),
            "constraints_count": len(constraints),
            "entities": [e.model_dump() for e in entities],
            "facts": [f.model_dump() for f in facts],
            "unknowns": [u.model_dump() for u in unknowns],
            "risks": [r.model_dump() for r in risks],
            "constraints": [c.model_dump() for c in constraints],
        }

    # --- 6. TRACE ---

    def trace_provenance(self, target_id: str) -> ProvenanceTrace:
        """Trace backward from any fact, claim, or entity to its root empirical observations and evidence URIs."""
        return self.store.trace_provenance(self.mission_id, target_id)
