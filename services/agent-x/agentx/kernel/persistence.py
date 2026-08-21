"""Agent-X Kernel Persistence Abstraction and In-Memory Store."""

import threading
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from agentx.kernel.events import KernelEvent
from agentx.kernel.models import Mission, Task


class StateStoreError(Exception):
    """Base exception for persistence errors."""

    pass


class EntityNotFoundError(StateStoreError):
    """Raised when an entity is not found in the store."""

    pass


class TaskLockError(StateStoreError):
    """Raised when a task lock cannot be acquired or is held by another worker."""

    pass


class StateStore(ABC):
    """Abstract persistence interface for Missions, Tasks, and Events."""

    @abstractmethod
    def save_mission(self, mission: Mission) -> None:
        """Persist or update a mission."""
        pass

    @abstractmethod
    def get_mission(self, mission_id: str) -> Mission | None:
        """Retrieve a mission by its ID."""
        pass

    @abstractmethod
    def list_missions(self) -> list[Mission]:
        """List all persisted missions."""
        pass

    @abstractmethod
    def save_task(self, task: Task) -> None:
        """Persist or update a task node."""
        pass

    @abstractmethod
    def get_task(self, mission_id: str, task_id: str) -> Task | None:
        """Retrieve a task node by mission ID and task ID."""
        pass

    @abstractmethod
    def list_tasks(self, mission_id: str) -> list[Task]:
        """List all tasks associated with a mission."""
        pass

    @abstractmethod
    def acquire_task_lock(
        self,
        mission_id: str,
        task_id: str,
        worker_id: str,
        lease_seconds: int = 300,
    ) -> bool:
        """Acquire a lease lock on a task for worker execution."""
        pass

    @abstractmethod
    def release_task_lock(self, mission_id: str, task_id: str, worker_id: str) -> bool:
        """Release a task lease lock."""
        pass

    @abstractmethod
    def record_event(self, event: KernelEvent) -> None:
        """Record an immutable domain event."""
        pass

    @abstractmethod
    def get_events(self, mission_id: str) -> list[KernelEvent]:
        """Retrieve all events for a given mission."""
        pass


class InMemoryStateStore(StateStore):
    """Thread-safe in-memory state store for testing and local execution."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._missions: dict[str, Mission] = {}
        self._tasks: dict[tuple[str, str], Task] = {}  # (mission_id, task_id) -> Task
        self._locks: dict[
            tuple[str, str], tuple[str, datetime]
        ] = {}  # (mission_id, task_id) -> (worker_id, expires_at)
        self._events: dict[str, list[KernelEvent]] = {}  # mission_id -> list[KernelEvent]

    def save_mission(self, mission: Mission) -> None:
        with self._lock:
            self._missions[mission.mission_id] = mission.model_copy(deep=True)

    def get_mission(self, mission_id: str) -> Mission | None:
        with self._lock:
            mission = self._missions.get(mission_id)
            return mission.model_copy(deep=True) if mission else None

    def list_missions(self) -> list[Mission]:
        with self._lock:
            return [m.model_copy(deep=True) for m in self._missions.values()]

    def save_task(self, task: Task) -> None:
        with self._lock:
            key = (task.mission_id, task.task_id)
            self._tasks[key] = task.model_copy(deep=True)

    def get_task(self, mission_id: str, task_id: str) -> Task | None:
        with self._lock:
            key = (mission_id, task_id)
            task = self._tasks.get(key)
            return task.model_copy(deep=True) if task else None

    def list_tasks(self, mission_id: str) -> list[Task]:
        with self._lock:
            return [
                task.model_copy(deep=True)
                for (m_id, _), task in self._tasks.items()
                if m_id == mission_id
            ]

    def acquire_task_lock(
        self,
        mission_id: str,
        task_id: str,
        worker_id: str,
        lease_seconds: int = 300,
    ) -> bool:
        with self._lock:
            key = (mission_id, task_id)
            task = self._tasks.get(key)
            if not task:
                raise EntityNotFoundError(f"Task '{task_id}' in mission '{mission_id}' not found")

            now = datetime.now(UTC)
            if key in self._locks:
                current_worker, expires_at = self._locks[key]
                if now < expires_at and current_worker != worker_id:
                    return False  # Lock held by someone else and active

            expires_at = datetime.fromtimestamp(now.timestamp() + lease_seconds, tz=UTC)
            self._locks[key] = (worker_id, expires_at)
            task.locked_by_worker_id = worker_id
            return True

    def release_task_lock(self, mission_id: str, task_id: str, worker_id: str) -> bool:
        with self._lock:
            key = (mission_id, task_id)
            if key not in self._locks:
                return True

            current_worker, _ = self._locks[key]
            if current_worker == worker_id:
                del self._locks[key]
                task = self._tasks.get(key)
                if task:
                    task.locked_by_worker_id = None
                return True
            return False

    def record_event(self, event: KernelEvent) -> None:
        with self._lock:
            if event.mission_id not in self._events:
                self._events[event.mission_id] = []
            self._events[event.mission_id].append(event.model_copy(deep=True))

    def get_events(self, mission_id: str) -> list[KernelEvent]:
        with self._lock:
            events = self._events.get(mission_id, [])
            return [e.model_copy(deep=True) for e in events]

    def clear(self) -> None:
        """Reset internal store state."""
        with self._lock:
            self._missions.clear()
            self._tasks.clear()
            self._locks.clear()
            self._events.clear()
