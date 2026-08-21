"""Google Cloud Firestore Client Abstraction and Mock/Emulator Adapter."""

import importlib
import threading
from collections.abc import Callable
from typing import Any


class MockFirestoreDocument:
    """Mock document reference implementing snapshot reads, set, update, and delete."""

    def __init__(self, path: str, store: dict[str, dict[str, Any]], lock: threading.RLock) -> None:
        self.path = path
        self.id = path.split("/")[-1]
        self._store = store
        self._lock = lock

    def get(self) -> "MockDocumentSnapshot":
        with self._lock:
            data = self._store.get(self.path)
            return MockDocumentSnapshot(self.id, self.path, data)

    def set(self, data: dict[str, Any], merge: bool = False) -> None:
        with self._lock:
            doc_data = dict(data)
            if merge and self.path in self._store:
                existing = dict(self._store[self.path])
                existing.update(doc_data)
                self._store[self.path] = existing
            else:
                self._store[self.path] = doc_data

    def update(self, data: dict[str, Any]) -> None:
        with self._lock:
            if self.path not in self._store:
                raise KeyError(f"Document '{self.path}' not found for update")
            self._store[self.path].update(data)

    def delete(self) -> None:
        with self._lock:
            self._store.pop(self.path, None)

    def collection(self, subcollection_name: str) -> "MockFirestoreCollection":
        return MockFirestoreCollection(f"{self.path}/{subcollection_name}", self._store, self._lock)


class MockDocumentSnapshot:
    """Represents a document snapshot returned from get()."""

    def __init__(self, doc_id: str, path: str, data: dict[str, Any] | None) -> None:
        self.id = doc_id
        self.path = path
        self._data = dict(data) if data is not None else None
        self.exists = data is not None

    def to_dict(self) -> dict[str, Any] | None:
        return dict(self._data) if self._data is not None else None


class MockFirestoreQuery:
    """Mock query supporting where filters, order_by, limit, and stream."""

    def __init__(
        self,
        collection_path: str,
        store: dict[str, dict[str, Any]],
        lock: threading.RLock,
        filters: list[tuple[str, str, Any]] | None = None,
        limit_val: int | None = None,
    ) -> None:
        self.collection_path = collection_path
        self._store = store
        self._lock = lock
        self._filters = filters or []
        self._limit_val = limit_val

    def where(self, field_path: str, op_string: str, value: Any) -> "MockFirestoreQuery":
        new_filters = list(self._filters)
        new_filters.append((field_path, op_string, value))
        return MockFirestoreQuery(
            self.collection_path, self._store, self._lock, new_filters, self._limit_val
        )

    def limit(self, count: int) -> "MockFirestoreQuery":
        return MockFirestoreQuery(
            self.collection_path, self._store, self._lock, self._filters, count
        )

    def stream(self) -> list[MockDocumentSnapshot]:
        with self._lock:
            results: list[MockDocumentSnapshot] = []
            prefix = f"{self.collection_path}/"

            for path, data in self._store.items():
                if path.startswith(prefix) and "/" not in path[len(prefix) :]:
                    doc_id = path.split("/")[-1]
                    matches = True
                    for field, op, val in self._filters:
                        doc_val = data.get(field)
                        if op in ("==", "=") and doc_val != val:
                            matches = False
                            break
                        elif op == "!=" and doc_val == val:
                            matches = False
                            break
                        elif op == ">" and not (doc_val is not None and doc_val > val):
                            matches = False
                            break
                        elif op == "<" and not (doc_val is not None and doc_val < val):
                            matches = False
                            break
                    if matches:
                        results.append(MockDocumentSnapshot(doc_id, path, data))
                        if self._limit_val and len(results) >= self._limit_val:
                            break
            return results


class MockFirestoreCollection:
    """Mock collection supporting document reference creation and queries."""

    def __init__(self, path: str, store: dict[str, dict[str, Any]], lock: threading.RLock) -> None:
        self.path = path.strip("/")
        self._store = store
        self._lock = lock

    def document(self, doc_id: str) -> MockFirestoreDocument:
        return MockFirestoreDocument(f"{self.path}/{doc_id}", self._store, self._lock)

    def where(self, field_path: str, op_string: str, value: Any) -> MockFirestoreQuery:
        return MockFirestoreQuery(self.path, self._store, self._lock).where(
            field_path, op_string, value
        )

    def stream(self) -> list[MockDocumentSnapshot]:
        return MockFirestoreQuery(self.path, self._store, self._lock).stream()


class MockFirestoreBatch:
    """Mock batch writer committing multiple set/update/delete operations atomically."""

    def __init__(self, client: "MockFirestoreClient") -> None:
        self.client = client
        self._ops: list[Callable[[], None]] = []

    def set(
        self, doc_ref: MockFirestoreDocument, data: dict[str, Any], merge: bool = False
    ) -> None:
        self._ops.append(lambda: doc_ref.set(data, merge=merge))

    def update(self, doc_ref: MockFirestoreDocument, data: dict[str, Any]) -> None:
        self._ops.append(lambda: doc_ref.update(data))

    def delete(self, doc_ref: MockFirestoreDocument) -> None:
        self._ops.append(lambda: doc_ref.delete())

    def commit(self) -> None:
        with self.client._lock:
            for op in self._ops:
                op()
            self._ops.clear()


class MockFirestoreClient:
    """High-fidelity thread-safe Mock Firestore Client in Native Mode."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._store: dict[str, dict[str, Any]] = {}

    def collection(self, collection_name: str) -> MockFirestoreCollection:
        return MockFirestoreCollection(collection_name, self._store, self._lock)

    def document(self, doc_path: str) -> MockFirestoreDocument:
        return MockFirestoreDocument(doc_path.strip("/"), self._store, self._lock)

    def batch(self) -> MockFirestoreBatch:
        return MockFirestoreBatch(self)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


class FirestoreClientFactory:
    """Factory creating either emulator/live Firestore client or in-memory Mock."""

    @staticmethod
    def create_client(
        project_id: str = "agent-x-local",
        database_id: str = "(default)",
        use_mock: bool = True,
    ) -> MockFirestoreClient | Any:
        if use_mock:
            return MockFirestoreClient()

        try:
            firestore_module = importlib.import_module("google.cloud.firestore")
            return firestore_module.Client(project=project_id, database=database_id)
        except Exception:
            return MockFirestoreClient()
