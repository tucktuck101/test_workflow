import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


log = logging.getLogger(__name__)


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class TrainerRun:
    run_id: str
    status: RunStatus
    config: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class InMemoryRunStore:
    def __init__(self):
        self._runs: Dict[str, TrainerRun] = {}
        self._lock = threading.Lock()

    def create(self, config: Dict[str, Any]) -> TrainerRun:
        run_id = str(uuid.uuid4())
        run = TrainerRun(run_id=run_id, status=RunStatus.PENDING, config=config or {}, metrics={"episodes": 0, "win_rate": 0.0, "loss": 0.0, "curriculum_phase": "bootcamp"})
        with self._lock:
            self._runs[run_id] = run
        return run

    def get(self, run_id: str) -> Optional[TrainerRun]:
        with self._lock:
            return self._runs.get(run_id)

    def update_status(self, run_id: str, status: RunStatus, error: Optional[str] = None) -> Optional[TrainerRun]:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return None
            if run.status in {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELED}:
                return run
            run.status = status
            run.updated_at = time.time()
            if error:
                run.error = error
            self._runs[run_id] = run
            return run

    def update_metrics(self, run_id: str, metrics: Dict[str, Any]) -> Optional[TrainerRun]:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return None
            run.metrics.update(metrics)
            run.updated_at = time.time()
            self._runs[run_id] = run
            return run


class TrainerOrchestrator:
    def start_run(self, config: Dict[str, Any] | None = None) -> TrainerRun:  # pragma: no cover - interface
        raise NotImplementedError

    def get_run(self, run_id: str) -> Optional[TrainerRun]:  # pragma: no cover - interface
        raise NotImplementedError

    def cancel_run(self, run_id: str) -> Optional[TrainerRun]:  # pragma: no cover - interface
        raise NotImplementedError

    def get_metrics(self, run_id: str) -> Optional[Dict[str, Any]]:  # pragma: no cover - interface
        raise NotImplementedError


class DummyTrainerOrchestrator(TrainerOrchestrator):
    """Local/dev orchestrator that simulates job lifecycle."""

    def __init__(self, store: Optional[InMemoryRunStore] = None, completion_delay: float = 0.1):
        self.store = store or InMemoryRunStore()
        self.completion_delay = completion_delay

    def start_run(self, config: Dict[str, Any] | None = None) -> TrainerRun:
        config = config or {}
        run = self.store.create(config)
        self.store.update_status(run.run_id, RunStatus.RUNNING)
        log.info("trainer run started", extra={"run_id": run.run_id, "config": config})

        def _complete():
            current = self.store.get(run.run_id)
            if not current or current.status != RunStatus.RUNNING:
                return
            # update some dummy metrics
            self.store.update_metrics(run.run_id, {"episodes": 10, "win_rate": 0.6, "loss": 0.4, "curriculum_phase": "bootcamp"})
            if config.get("fail"):
                self.store.update_status(run.run_id, RunStatus.FAILED, error="simulated_failure")
                log.error("trainer run failed", extra={"run_id": run.run_id})
            else:
                self.store.update_status(run.run_id, RunStatus.SUCCEEDED)
                log.info("trainer run completed", extra={"run_id": run.run_id})

        timer = threading.Timer(self.completion_delay, _complete)
        timer.daemon = True
        timer.start()
        return run

    def get_run(self, run_id: str) -> Optional[TrainerRun]:
        return self.store.get(run_id)

    def cancel_run(self, run_id: str) -> Optional[TrainerRun]:
        run = self.store.get(run_id)
        if not run:
            return None
        if run.status in {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELED}:
            return run
        updated = self.store.update_status(run_id, RunStatus.CANCELED)
        log.info("trainer run canceled", extra={"run_id": run_id})
        return updated

    def get_metrics(self, run_id: str) -> Optional[Dict[str, Any]]:
        run = self.store.get(run_id)
        if not run:
            return None
        return run.metrics


class ComposeTrainerOrchestrator(TrainerOrchestrator):
    """Placeholder for docker-compose orchestration."""

    def __init__(self, store: Optional[InMemoryRunStore] = None):
        self.store = store or InMemoryRunStore()

    def start_run(self, config: Dict[str, Any] | None = None) -> TrainerRun:
        # For now delegate to dummy behavior; hook into docker compose if needed.
        return DummyTrainerOrchestrator(self.store).start_run(config)

    def get_run(self, run_id: str) -> Optional[TrainerRun]:
        return self.store.get(run_id)

    def cancel_run(self, run_id: str) -> Optional[TrainerRun]:
        return DummyTrainerOrchestrator(self.store).cancel_run(run_id)

    def get_metrics(self, run_id: str) -> Optional[Dict[str, Any]]:
        run = self.store.get(run_id)
        return run.metrics if run else None


class KubernetesTrainerOrchestrator(TrainerOrchestrator):
    """Placeholder for k8s job orchestration."""

    def __init__(self, store: Optional[InMemoryRunStore] = None):
        self.store = store or InMemoryRunStore()

    def start_run(self, config: Dict[str, Any] | None = None) -> TrainerRun:
        # Stubbed to dummy behavior; swap to k8s Job creation when available.
        return DummyTrainerOrchestrator(self.store).start_run(config)

    def get_run(self, run_id: str) -> Optional[TrainerRun]:
        return self.store.get(run_id)

    def cancel_run(self, run_id: str) -> Optional[TrainerRun]:
        return DummyTrainerOrchestrator(self.store).cancel_run(run_id)

    def get_metrics(self, run_id: str) -> Optional[Dict[str, Any]]:
        run = self.store.get(run_id)
        return run.metrics if run else None
