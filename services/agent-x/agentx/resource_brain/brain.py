"""Agent-X Resource Brain Central Controller."""

import threading
from datetime import UTC, datetime
from typing import Any

from agentx.kernel.events import EventBus, EventType, ResourceEvent
from agentx.kernel.models import Task
from agentx.resource_brain.ledger import ResourceLedger
from agentx.resource_brain.pricing import calculate_llm_cost
from agentx.resource_brain.router import ModelRouter
from agentx.resource_brain.schemas import (
    AgentAvailabilityPool,
    AllocationChangeEvent,
    AllocationDecision,
    HumanAttentionTracker,
    ModelTier,
    ResourceConsumption,
    ResourceDimension,
    ResourceMetricTuple,
    ResourceMonitorSnapshot,
    ResourcePrediction,
    ResourceReservation,
    StorageQuotaTracker,
    ToolAvailabilityPool,
)
from agentx_common.schemas import MissionBudget


class ResourceExhaustedError(Exception):
    """Raised when a hard resource cap (budget, tokens, deadline) is exceeded."""

    pass


class ResourceBrain:
    """Quantitative governance controller managing budgets, tokens, SLAs, quotas, agent slots, and model routing."""

    def __init__(
        self,
        mission_id: str,
        budget: MissionBudget | None = None,
        deadline_seconds: int = 3600,
        event_bus: EventBus | None = None,
    ) -> None:
        self.mission_id = mission_id
        self.budget: MissionBudget = budget or MissionBudget()
        self.deadline_seconds = deadline_seconds
        self.event_bus: EventBus = event_bus or EventBus()
        self.ledger: ResourceLedger = ResourceLedger(mission_id=mission_id)

        self._lock = threading.RLock()
        self.agent_pool = AgentAvailabilityPool()
        self.tool_pool = ToolAvailabilityPool()
        self.storage_tracker = StorageQuotaTracker()
        self.human_attention = HumanAttentionTracker()

        self._active_reservations: dict[str, ResourceReservation] = {}
        self._task_reservations: dict[str, str] = {}  # task_id -> reservation_id
        self._allocation_history: list[AllocationChangeEvent] = []

        self._budget_warning_emitted = False
        self._deadline_warning_emitted = False

    # --- 1. PREDICTION & ROUTING ---

    def predict_task_resources(
        self,
        task: Task,
        reasoning_depth: float = 0.5,
        code_size: float = 0.3,
        tool_count: int = 1,
        is_exploratory: bool = False,
        requires_deep_reasoning: bool = False,
    ) -> ResourcePrediction:
        """Predict required model, token volume, financial cost, and execution duration."""
        return ModelRouter.predict_and_route(
            task=task,
            reasoning_depth=reasoning_depth,
            code_size=code_size,
            tool_count=tool_count,
            is_exploratory=is_exploratory,
            requires_deep_reasoning=requires_deep_reasoning,
        )

    # --- 2. RESERVATION & ALLOCATION ---

    def request_allocation(
        self,
        task: Task,
        reasoning_depth: float = 0.5,
        is_exploratory: bool = False,
        required_tools: list[str] | None = None,
    ) -> AllocationDecision:
        """Evaluate resource availability, reserve compute and agent slots, and emit an explainable decision."""
        with self._lock:
            tools = required_tools or []
            prediction = self.predict_task_resources(
                task=task,
                reasoning_depth=reasoning_depth,
                is_exploratory=is_exploratory,
                tool_count=len(tools),
            )

            current_spent = self.ledger.cumulative_usd_spent
            active_reserved_usd = sum(
                r.reserved_cost_usd for r in self._active_reservations.values() if r.is_active
            )
            total_committed_usd = (
                current_spent + active_reserved_usd + prediction.predicted_cost_usd
            )

            # A. Check Financial Budget
            if total_committed_usd > self.budget.max_usd_limit:
                refusal = (
                    f"Budget Exhausted: Committed spend (${total_committed_usd:.4f}) exceeds "
                    f"mission budget ceiling (${self.budget.max_usd_limit:.2f}). "
                    f"Spent: ${current_spent:.4f}, Active Reservations: ${active_reserved_usd:.4f}."
                )
                self.event_bus.publish(
                    ResourceEvent(
                        mission_id=self.mission_id,
                        task_id=task.task_id,
                        event_type=EventType.BUDGET_EXHAUSTED,
                        mutation_type="EXHAUSTED",
                        amount_usd=prediction.predicted_cost_usd,
                        details={"reason": refusal},
                    )
                )
                return AllocationDecision(
                    task_id=task.task_id,
                    is_granted=False,
                    explanation="Allocation refused due to mission budget depletion.",
                    refusal_reason=refusal,
                )

            # B. Check Deadline Pressure
            current_duration = self.ledger.cumulative_duration_seconds
            if current_duration + prediction.predicted_duration_seconds > self.deadline_seconds:
                self.event_bus.publish(
                    ResourceEvent(
                        mission_id=self.mission_id,
                        task_id=task.task_id,
                        event_type=EventType.DEADLINE_WARNING,
                        mutation_type="WARNING",
                        duration_seconds=prediction.predicted_duration_seconds,
                        details={"message": "Task duration risks exceeding mission deadline SLA."},
                    )
                )

            # C. Check Agent Capacity
            role_key = task.agent_role.value
            max_slots = self.agent_pool.max_slots_per_role.get(role_key, 2)
            active_slots = len(self.agent_pool.active_leases.get(role_key, []))
            if active_slots >= max_slots:
                refusal = f"Agent concurrency ceiling reached for role '{role_key}' ({active_slots}/{max_slots} slots active)."
                return AllocationDecision(
                    task_id=task.task_id,
                    is_granted=False,
                    explanation="Allocation deferred due to worker capacity.",
                    refusal_reason=refusal,
                )

            # D. Check Exclusive Tool Locks
            for tool in tools:
                if tool in self.tool_pool.exclusive_tools:
                    if tool in self.tool_pool.active_tool_locks:
                        holding_task = self.tool_pool.active_tool_locks[tool]
                        refusal = (
                            f"Exclusive tool '{tool}' is currently locked by task '{holding_task}'."
                        )
                        return AllocationDecision(
                            task_id=task.task_id,
                            is_granted=False,
                            explanation="Allocation deferred due to tool lock contention.",
                            refusal_reason=refusal,
                        )

            # E. Grant Allocation and Record Reservation
            reservation = ResourceReservation(
                mission_id=self.mission_id,
                task_id=task.task_id,
                model=prediction.predicted_model,
                reserved_tokens=prediction.predicted_total_tokens,
                reserved_cost_usd=prediction.predicted_cost_usd,
                reserved_duration_seconds=prediction.predicted_duration_seconds,
                reserved_agent_role=task.agent_role,
                reserved_tools=tools,
            )

            self._active_reservations[reservation.reservation_id] = reservation
            self._task_reservations[task.task_id] = reservation.reservation_id

            # Acquire Leases
            self.agent_pool.active_leases.setdefault(role_key, []).append(task.task_id)
            for tool in tools:
                if tool in self.tool_pool.exclusive_tools:
                    self.tool_pool.active_tool_locks[tool] = task.task_id

            # Record Ledger Entry
            self.ledger.record_mutation(
                mutation_type="RESERVATION",
                task_id=task.task_id,
                amount_usd=reservation.reserved_cost_usd,
                tokens=reservation.reserved_tokens,
                duration_seconds=reservation.reserved_duration_seconds,
                details={
                    "reservation_id": reservation.reservation_id,
                    "model": reservation.model.value,
                },
            )

            # Emit Event
            self.event_bus.publish(
                ResourceEvent(
                    mission_id=self.mission_id,
                    task_id=task.task_id,
                    event_type=EventType.RESOURCE_RESERVED,
                    mutation_type="RESERVATION",
                    amount_usd=reservation.reserved_cost_usd,
                    tokens=reservation.reserved_tokens,
                    details={
                        "reservation_id": reservation.reservation_id,
                        "model": reservation.model.value,
                        "agent_role": task.agent_role.value,
                    },
                )
            )

            explanation = (
                f"Granted allocation for task '{task.name}' ({task.agent_role.value}). "
                f"{prediction.explanation} "
                f"Reserved: {prediction.predicted_total_tokens:,} tokens, "
                f"${prediction.predicted_cost_usd:.4f} USD, "
                f"{prediction.predicted_duration_seconds}s timeout."
            )

            return AllocationDecision(
                task_id=task.task_id,
                is_granted=True,
                selected_model=prediction.predicted_model,
                allocated_tokens=prediction.predicted_total_tokens,
                timeout_seconds=prediction.predicted_duration_seconds,
                reserved_cost_usd=prediction.predicted_cost_usd,
                assigned_role=task.agent_role,
                reservation_id=reservation.reservation_id,
                explanation=explanation,
            )

    # --- 3. CONSUMPTION & METERING ---

    def record_consumption(
        self,
        task_id: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        actual_duration_seconds: int = 0,
        storage_bytes: int = 0,
        model: ModelTier | None = None,
    ) -> ResourceConsumption:
        """Record actual empirical resource consumption, update ledger, and check budget/deadline thresholds."""
        with self._lock:
            res_id = self._task_reservations.get(task_id)
            reservation = self._active_reservations.get(res_id) if res_id else None
            assigned_model = model or (
                reservation.model if reservation else ModelTier.GEMINI_2_5_FLASH
            )

            actual_cost = calculate_llm_cost(
                model=assigned_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_tokens=cached_tokens,
            )
            total_tokens = input_tokens + output_tokens

            consumption = ResourceConsumption(
                mission_id=self.mission_id,
                task_id=task_id,
                model=assigned_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_tokens=cached_tokens,
                total_tokens=total_tokens,
                actual_cost_usd=actual_cost,
                actual_duration_seconds=actual_duration_seconds,
                storage_bytes=storage_bytes,
            )

            # Record Ledger mutation
            self.ledger.record_mutation(
                mutation_type="CONSUMPTION",
                task_id=task_id,
                amount_usd=actual_cost,
                tokens=total_tokens,
                duration_seconds=actual_duration_seconds,
                storage_bytes=storage_bytes,
                details={
                    "model": assigned_model.value,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cached_tokens": cached_tokens,
                },
            )

            # Synchronize budget model
            self.budget.current_usd_spent = self.ledger.cumulative_usd_spent
            self.budget.current_tokens_used = self.ledger.cumulative_tokens_used
            self.budget.current_execution_time_seconds = self.ledger.cumulative_duration_seconds

            # Emit Consumption Event
            self.event_bus.publish(
                ResourceEvent(
                    mission_id=self.mission_id,
                    task_id=task_id,
                    event_type=EventType.RESOURCE_CONSUMED,
                    mutation_type="CONSUMPTION",
                    amount_usd=actual_cost,
                    tokens=total_tokens,
                    details={"model": assigned_model.value, "duration": actual_duration_seconds},
                )
            )

            # Check 80% Budget Warning
            if (
                self.budget.current_usd_spent >= 0.80 * self.budget.max_usd_limit
                and not self._budget_warning_emitted
            ):
                self._budget_warning_emitted = True
                self.event_bus.publish(
                    ResourceEvent(
                        mission_id=self.mission_id,
                        task_id=task_id,
                        event_type=EventType.BUDGET_WARNING,
                        mutation_type="WARNING",
                        amount_usd=self.budget.current_usd_spent,
                        details={
                            "message": f"Mission has consumed 80% of budget cap (${self.budget.current_usd_spent:.2f}/${self.budget.max_usd_limit:.2f})"
                        },
                    )
                )

            # Check 100% Budget Exhaustion
            if self.budget.current_usd_spent >= self.budget.max_usd_limit:
                self.event_bus.publish(
                    ResourceEvent(
                        mission_id=self.mission_id,
                        task_id=task_id,
                        event_type=EventType.BUDGET_EXHAUSTED,
                        mutation_type="EXHAUSTED",
                        amount_usd=self.budget.current_usd_spent,
                        details={
                            "message": f"Hard budget ceiling reached (${self.budget.current_usd_spent:.2f}/${self.budget.max_usd_limit:.2f})"
                        },
                    )
                )

            # Check 80% Deadline Warning
            if (
                self.budget.current_execution_time_seconds >= 0.80 * self.deadline_seconds
                and not self._deadline_warning_emitted
            ):
                self._deadline_warning_emitted = True
                self.event_bus.publish(
                    ResourceEvent(
                        mission_id=self.mission_id,
                        task_id=task_id,
                        event_type=EventType.DEADLINE_WARNING,
                        mutation_type="WARNING",
                        duration_seconds=self.budget.current_execution_time_seconds,
                        details={
                            "message": f"80% of SLA deadline consumed ({self.budget.current_execution_time_seconds}s/{self.deadline_seconds}s)"
                        },
                    )
                )

            return consumption

    # --- 4. RELEASE & REALLOCATION ---

    def release_reservation(self, task_id: str, reason: str = "Task completed") -> None:
        """Release active worker leases, tool locks, and unconsumed reservation holds."""
        with self._lock:
            res_id = self._task_reservations.pop(task_id, None)
            if not res_id or res_id not in self._active_reservations:
                return

            reservation = self._active_reservations.pop(res_id)
            reservation.is_active = False

            # Release Agent Lease
            role_key = reservation.reserved_agent_role.value
            if role_key in self.agent_pool.active_leases:
                if task_id in self.agent_pool.active_leases[role_key]:
                    self.agent_pool.active_leases[role_key].remove(task_id)

            # Release Tool Locks
            for tool in reservation.reserved_tools:
                if self.tool_pool.active_tool_locks.get(tool) == task_id:
                    self.tool_pool.active_tool_locks.pop(tool, None)

            # Record Ledger Mutation
            self.ledger.record_mutation(
                mutation_type="RELEASE",
                task_id=task_id,
                amount_usd=reservation.reserved_cost_usd,
                tokens=reservation.reserved_tokens,
                details={"reservation_id": res_id, "reason": reason},
            )

            # Emit Event
            self.event_bus.publish(
                ResourceEvent(
                    mission_id=self.mission_id,
                    task_id=task_id,
                    event_type=EventType.RESOURCE_RELEASED,
                    mutation_type="RELEASE",
                    amount_usd=reservation.reserved_cost_usd,
                    tokens=reservation.reserved_tokens,
                    details={"reservation_id": res_id, "reason": reason},
                )
            )

    def record_allocation_change(
        self,
        dimension: ResourceDimension,
        target_name: str,
        delta: float,
        unit: str,
        trigger_type: str,
        reason: str,
        previous_allocated: float | None = None,
        new_allocated: float | None = None,
    ) -> AllocationChangeEvent:
        """Record and broadcast an explicit causal explanation for an allocation change."""
        with self._lock:
            prev = previous_allocated if previous_allocated is not None else 0.0
            new_val = new_allocated if new_allocated is not None else (prev + delta)
            event = AllocationChangeEvent(
                mission_id=self.mission_id,
                dimension=dimension,
                target_name=target_name,
                previous_allocated=prev,
                new_allocated=new_val,
                delta=delta,
                unit=unit,
                trigger_type=trigger_type,
                reason=reason,
            )
            self._allocation_history.append(event)
            self.event_bus.publish(
                ResourceEvent(
                    mission_id=self.mission_id,
                    task_id=target_name,
                    event_type=EventType.RESOURCE_REALLOCATED,
                    mutation_type="REALLOCATION",
                    amount_usd=delta if unit == "USD" else 0.0,
                    tokens=int(delta) if unit == "tokens" else 0,
                    details={
                        "change_id": event.change_id,
                        "dimension": dimension.value,
                        "trigger_type": trigger_type,
                        "reason": reason,
                        "delta": delta,
                        "unit": unit,
                    },
                )
            )
            return event

    def reallocate_budget(
        self,
        from_task_id: str,
        to_task_id: str,
        usd_amount: float,
        tokens: int,
        reason: str,
        trigger_type: str = "DYNAMIC_REALLOCATION",
    ) -> None:
        """Dynamically transfer unconsumed budget and tokens between DAG branches with causal explanation."""
        with self._lock:
            self.ledger.record_mutation(
                mutation_type="REALLOCATION",
                task_id=to_task_id,
                amount_usd=usd_amount,
                tokens=tokens,
                details={"from_task_id": from_task_id, "to_task_id": to_task_id, "reason": reason},
            )

            # Record in allocation history
            event = AllocationChangeEvent(
                mission_id=self.mission_id,
                dimension=ResourceDimension.BUDGET
                if usd_amount > 0
                else ResourceDimension.API_USAGE,
                target_name=to_task_id,
                previous_allocated=0.0,
                new_allocated=usd_amount,
                delta=usd_amount if usd_amount > 0 else float(tokens),
                unit="USD" if usd_amount > 0 else "tokens",
                trigger_type=trigger_type,
                reason=reason,
            )
            self._allocation_history.append(event)

            self.event_bus.publish(
                ResourceEvent(
                    mission_id=self.mission_id,
                    task_id=to_task_id,
                    event_type=EventType.RESOURCE_REALLOCATED,
                    mutation_type="REALLOCATION",
                    amount_usd=usd_amount,
                    tokens=tokens,
                    details={
                        "from_task_id": from_task_id,
                        "to_task_id": to_task_id,
                        "reason": reason,
                        "change_id": event.change_id,
                        "trigger_type": trigger_type,
                    },
                )
            )

    # --- 5. STORAGE & HUMAN ATTENTION GOVERNANCE ---

    def record_storage(self, bytes_delta: int) -> int:
        """Track artifact storage consumption and enforce hard limits."""
        with self._lock:
            new_total = self.storage_tracker.current_storage_bytes + bytes_delta
            if new_total > self.storage_tracker.max_storage_bytes:
                raise ResourceExhaustedError(
                    f"Storage quota exceeded: {new_total} bytes > {self.storage_tracker.max_storage_bytes} bytes limit."
                )
            self.storage_tracker.current_storage_bytes = new_total
            return new_total

    def request_human_attention(self, reason: str, task_id: str | None = None) -> bool:
        """Rate-limit operator interrupts to prevent notification fatigue."""
        with self._lock:
            if (
                self.human_attention.current_interrupts
                >= self.human_attention.max_interrupts_allowed
            ):
                return False

            self.human_attention.current_interrupts += 1
            self.human_attention.last_interaction_at = datetime.now(UTC)

            self.event_bus.publish(
                ResourceEvent(
                    mission_id=self.mission_id,
                    task_id=task_id,
                    event_type=EventType.HUMAN_ATTENTION_REQUESTED,
                    mutation_type="HUMAN_ATTENTION",
                    details={
                        "reason": reason,
                        "interrupt_number": self.human_attention.current_interrupts,
                    },
                )
            )
            return True

    # --- 6. TELEMETRY & SNAPSHOTS ---

    def get_telemetry_snapshot(self) -> dict[str, Any]:
        """Aggregate comprehensive resource state for Mission Control."""
        with self._lock:
            return {
                "mission_id": self.mission_id,
                "usd_spent": self.ledger.cumulative_usd_spent,
                "usd_limit": self.budget.max_usd_limit,
                "usd_remaining": max(
                    0.0, self.budget.max_usd_limit - self.ledger.cumulative_usd_spent
                ),
                "tokens_used": self.ledger.cumulative_tokens_used,
                "tokens_limit": self.budget.max_total_tokens,
                "execution_time_seconds": self.ledger.cumulative_duration_seconds,
                "deadline_seconds": self.deadline_seconds,
                "deadline_remaining_seconds": max(
                    0, self.deadline_seconds - self.ledger.cumulative_duration_seconds
                ),
                "active_reservations_count": len(self._active_reservations),
                "active_agent_leases": dict(self.agent_pool.active_leases),
                "active_tool_locks": dict(self.tool_pool.active_tool_locks),
                "storage_bytes_used": self.storage_tracker.current_storage_bytes,
                "human_interrupts_count": self.human_attention.current_interrupts,
                "ledger_entries_count": len(self.ledger.get_entries()),
            }

    def get_monitor_snapshot(self) -> ResourceMonitorSnapshot:
        """Generate full multi-dimensional Resource Monitor breakdown with causal history."""
        with self._lock:
            # 1. Budget ($ USD)
            budget_alloc = float(self.budget.max_usd_limit)
            budget_consumed = float(self.ledger.cumulative_usd_spent)
            budget_reserved = float(
                sum(r.reserved_cost_usd for r in self._active_reservations.values() if r.is_active)
            )
            budget_remaining = max(0.0, budget_alloc - budget_consumed - budget_reserved)

            # 2. Time (Seconds)
            time_alloc = float(self.deadline_seconds)
            time_consumed = float(self.ledger.cumulative_duration_seconds)
            time_reserved = float(
                sum(
                    r.reserved_duration_seconds
                    for r in self._active_reservations.values()
                    if r.is_active
                )
            )
            time_remaining = max(0.0, time_alloc - time_consumed - time_reserved)

            # 3. Compute (Parallel Worker Slots)
            total_compute_slots = 10.0
            active_leased_slots = float(
                sum(len(leases) for leases in self.agent_pool.active_leases.values())
            )
            reserved_compute_slots = float(len(self._active_reservations))
            remaining_compute = max(
                0.0, total_compute_slots - active_leased_slots - reserved_compute_slots
            )

            # 4. API Usage (Model Tokens)
            tokens_alloc = float(self.budget.max_total_tokens)
            tokens_consumed = float(self.ledger.cumulative_tokens_used)
            tokens_reserved = float(
                sum(r.reserved_tokens for r in self._active_reservations.values() if r.is_active)
            )
            tokens_remaining = max(0.0, tokens_alloc - tokens_consumed - tokens_reserved)

            # 5. Agent Capacity (Total Agent Slots across roles)
            total_agent_slots = float(sum(self.agent_pool.max_slots_per_role.values()))
            total_agent_consumed = active_leased_slots
            total_agent_reserved = float(len(self._active_reservations))
            total_agent_remaining = max(
                0.0, total_agent_slots - total_agent_consumed - total_agent_reserved
            )

            # 6. Tool Usage (Permissible tool invocations)
            total_tool_quota = 100.0
            tool_consumed = float(
                len([e for e in self.ledger.get_entries() if e.mutation_type == "CONSUMPTION"])
            )
            tool_reserved = float(len(self.tool_pool.active_tool_locks))
            tool_remaining = max(0.0, total_tool_quota - tool_consumed - tool_reserved)

            # Per-Agent breakdown
            agent_breakdown: dict[str, ResourceMetricTuple] = {}
            for role, max_s in self.agent_pool.max_slots_per_role.items():
                active_s = float(len(self.agent_pool.active_leases.get(role, [])))
                res_s = float(
                    sum(
                        1
                        for r in self._active_reservations.values()
                        if r.is_active and r.reserved_agent_role.value == role
                    )
                )
                rem_s = max(0.0, float(max_s) - active_s - res_s)
                agent_breakdown[role] = ResourceMetricTuple(
                    allocated=float(max_s),
                    consumed=active_s,
                    remaining=rem_s,
                    reserved=res_s,
                    unit="slots",
                )

            # Per-Tool breakdown
            tool_breakdown: dict[str, ResourceMetricTuple] = {}
            for tool_name in [
                "web_research",
                "calculator",
                "data_analysis",
                "document_reader",
                "file_operations",
                "artifact_generation",
            ]:
                is_locked = tool_name in self.tool_pool.active_tool_locks
                tool_breakdown[tool_name] = ResourceMetricTuple(
                    allocated=20.0,
                    consumed=0.0,
                    remaining=19.0 if is_locked else 20.0,
                    reserved=1.0 if is_locked else 0.0,
                    unit="runs",
                )

            dimensions = {
                "budget": ResourceMetricTuple(
                    allocated=budget_alloc,
                    consumed=budget_consumed,
                    remaining=budget_remaining,
                    reserved=budget_reserved,
                    unit="USD",
                ),
                "time": ResourceMetricTuple(
                    allocated=time_alloc,
                    consumed=time_consumed,
                    remaining=time_remaining,
                    reserved=time_reserved,
                    unit="seconds",
                ),
                "compute": ResourceMetricTuple(
                    allocated=total_compute_slots,
                    consumed=active_leased_slots,
                    remaining=remaining_compute,
                    reserved=reserved_compute_slots,
                    unit="slots",
                ),
                "api_usage": ResourceMetricTuple(
                    allocated=tokens_alloc,
                    consumed=tokens_consumed,
                    remaining=tokens_remaining,
                    reserved=tokens_reserved,
                    unit="tokens",
                ),
                "agent_capacity": ResourceMetricTuple(
                    allocated=total_agent_slots,
                    consumed=total_agent_consumed,
                    remaining=total_agent_remaining,
                    reserved=total_agent_reserved,
                    unit="slots",
                ),
                "tool_usage": ResourceMetricTuple(
                    allocated=total_tool_quota,
                    consumed=tool_consumed,
                    remaining=tool_remaining,
                    reserved=tool_reserved,
                    unit="runs",
                ),
            }

            return ResourceMonitorSnapshot(
                mission_id=self.mission_id,
                dimensions=dimensions,
                agent_breakdown=agent_breakdown,
                tool_breakdown=tool_breakdown,
                reallocation_history=list(self._allocation_history),
            )
