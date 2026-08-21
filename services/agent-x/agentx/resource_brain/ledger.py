"""Agent-X Resource Ledger for Transactional Auditability."""

import threading
from datetime import UTC, datetime
from typing import Any

from agentx.resource_brain.schemas import ResourceLedgerEntry


class ResourceLedger:
    """Thread-safe transactional audit ledger tracking every resource mutation in a mission."""

    def __init__(self, mission_id: str) -> None:
        self.mission_id = mission_id
        self._lock = threading.RLock()
        self._entries: list[ResourceLedgerEntry] = []
        self._cumulative_usd_spent: float = 0.0
        self._cumulative_tokens_used: int = 0
        self._cumulative_duration_seconds: int = 0
        self._current_storage_bytes: int = 0

    def record_mutation(
        self,
        mutation_type: str,
        task_id: str | None = None,
        amount_usd: float = 0.0,
        tokens: int = 0,
        duration_seconds: int = 0,
        storage_bytes: int = 0,
        details: dict[str, Any] | None = None,
    ) -> ResourceLedgerEntry:
        """Record an immutable transaction in the ledger."""
        with self._lock:
            if mutation_type == "CONSUMPTION":
                self._cumulative_usd_spent += amount_usd
                self._cumulative_tokens_used += tokens
                self._cumulative_duration_seconds += duration_seconds
                self._current_storage_bytes += storage_bytes

            entry = ResourceLedgerEntry(
                mission_id=self.mission_id,
                task_id=task_id,
                mutation_type=mutation_type,
                amount_usd=amount_usd,
                tokens=tokens,
                duration_seconds=duration_seconds,
                storage_bytes=storage_bytes,
                details=details or {},
                running_usd_spent=round(self._cumulative_usd_spent, 6),
                running_tokens_used=self._cumulative_tokens_used,
                timestamp=datetime.now(UTC),
            )
            self._entries.append(entry)
            return entry

    def get_entries(self, task_id: str | None = None) -> list[ResourceLedgerEntry]:
        with self._lock:
            if task_id is None:
                return list(self._entries)
            return [e for e in self._entries if e.task_id == task_id]

    @property
    def cumulative_usd_spent(self) -> float:
        with self._lock:
            return round(self._cumulative_usd_spent, 6)

    @property
    def cumulative_tokens_used(self) -> int:
        with self._lock:
            return self._cumulative_tokens_used

    @property
    def cumulative_duration_seconds(self) -> int:
        with self._lock:
            return self._cumulative_duration_seconds

    @property
    def current_storage_bytes(self) -> int:
        with self._lock:
            return self._current_storage_bytes
