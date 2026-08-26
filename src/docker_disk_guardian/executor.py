"""Cleanup execution with policy revalidation immediately before deletion."""

import signal
from collections.abc import Callable
from datetime import UTC, datetime
from threading import Event
from types import FrameType
from typing import Any

from docker_disk_guardian.config import CleanupPolicy
from docker_disk_guardian.models import (
    CleanupPlan,
    ExecutionItem,
    ExecutionResult,
    ExecutionStatus,
    Inventory,
    ResourceType,
)
from docker_disk_guardian.planner import CleanupPlanner
from docker_disk_guardian.ports import DockerGateway


class SignalInterruption:
    """Convert SIGINT into a cooperative stop between deletion operations."""

    def __init__(self) -> None:
        self._event = Event()
        self._previous: Any = None

    def __enter__(self) -> "SignalInterruption":
        self._previous = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle)
        return self

    def __exit__(self, *_args: object) -> None:
        if self._previous is not None:
            signal.signal(signal.SIGINT, self._previous)

    def requested(self) -> bool:
        return self._event.is_set()

    def request(self) -> None:
        self._event.set()

    def _handle(self, _signum: int, _frame: FrameType | None) -> None:
        self.request()


class CleanupExecutor:
    def __init__(
        self,
        gateway: DockerGateway,
        policy: CleanupPolicy,
        *,
        clock: Callable[[], datetime] | None = None,
        should_stop: Callable[[], bool] | None = None,
    ) -> None:
        self._gateway = gateway
        self._policy = policy
        self._clock = clock or (lambda: datetime.now(UTC))
        self._should_stop = should_stop or (lambda: False)

    def execute(self, requested_plan: CleanupPlan, current_inventory: Inventory) -> ExecutionResult:
        """Re-plan current state, then execute only still-eligible requested candidates."""
        started_at = self._clock()
        verified_plan = CleanupPlanner(self._policy, clock=lambda: started_at).create_plan(
            current_inventory
        )
        verified = {
            (item.resource_type, item.resource_id): item for item in verified_plan.candidates
        }
        items: list[ExecutionItem] = []
        interrupted = False

        for requested in requested_plan.candidates:
            if self._should_stop():
                interrupted = True
                break
            key = (requested.resource_type, requested.resource_id)
            if key not in verified:
                items.append(
                    ExecutionItem(
                        resource_type=requested.resource_type,
                        resource_id=requested.resource_id,
                        resource_name=requested.resource_name,
                        status=ExecutionStatus.SKIPPED,
                        message="resource is no longer eligible under the current policy and state",
                    )
                )
                continue
            if requested.resource_type == ResourceType.BUILD_CACHE:
                items.append(
                    ExecutionItem(
                        resource_type=requested.resource_type,
                        resource_id=requested.resource_id,
                        resource_name=requested.resource_name,
                        status=ExecutionStatus.SKIPPED,
                        message="targeted build-cache deletion is not supported safely",
                    )
                )
                continue
            try:
                self._gateway.remove(requested.resource_type, requested.resource_id)
            except Exception as exc:  # Docker SDK errors vary by resource endpoint.
                items.append(
                    ExecutionItem(
                        resource_type=requested.resource_type,
                        resource_id=requested.resource_id,
                        resource_name=requested.resource_name,
                        status=ExecutionStatus.FAILED,
                        message=f"removal failed: {exc}",
                    )
                )
            else:
                items.append(
                    ExecutionItem(
                        resource_type=requested.resource_type,
                        resource_id=requested.resource_id,
                        resource_name=requested.resource_name,
                        status=ExecutionStatus.SUCCEEDED,
                        message="resource removed",
                    )
                )

        return ExecutionResult(
            started_at=started_at,
            completed_at=self._clock(),
            items=tuple(items),
            interrupted=interrupted,
        )
