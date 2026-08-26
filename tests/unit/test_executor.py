from datetime import UTC, datetime, timedelta

from docker_disk_guardian.config import CleanupPolicy
from docker_disk_guardian.executor import CleanupExecutor, SignalInterruption
from docker_disk_guardian.models import (
    CleanupDecision,
    CleanupPlan,
    ContainerResource,
    ContainerState,
    ExecutionStatus,
    Inventory,
)
from tests.fakes import FakeDockerGateway

NOW = datetime(2026, 4, 14, tzinfo=UTC)


def _candidate_plan() -> CleanupPlan:
    return CleanupPlan(
        generated_at=NOW,
        decisions=(
            CleanupDecision(
                resource_type="container",
                resource_id="container-1",
                resource_name="job",
                status="candidate",
                reasons=("stopped container exceeds retention",),
            ),
        ),
    )


def test_executes_candidate_that_is_still_safe() -> None:
    container = ContainerResource(
        id="container-1",
        name="job",
        created_at=NOW - timedelta(days=10),
        state=ContainerState.STOPPED,
        image_id="image-1",
    )
    inventory = Inventory(collected_at=NOW, containers=(container,))
    gateway = FakeDockerGateway()

    result = CleanupExecutor(gateway, CleanupPolicy(), clock=lambda: NOW).execute(
        _candidate_plan(), inventory
    )

    assert gateway.removed == [(container.resource_type, "container-1")]
    assert result.items[0].status == ExecutionStatus.SUCCEEDED


def test_revalidation_blocks_container_that_started_running() -> None:
    container = ContainerResource(
        id="container-1",
        name="job",
        created_at=NOW - timedelta(days=10),
        state=ContainerState.RUNNING,
        image_id="image-1",
    )
    inventory = Inventory(collected_at=NOW, containers=(container,))
    gateway = FakeDockerGateway()

    result = CleanupExecutor(gateway, CleanupPolicy(), clock=lambda: NOW).execute(
        _candidate_plan(), inventory
    )

    assert gateway.removed == []
    assert result.items[0].status == ExecutionStatus.SKIPPED
    assert "no longer eligible" in result.items[0].message


def test_partial_failure_does_not_hide_successful_operations() -> None:
    containers = tuple(
        ContainerResource(
            id=f"container-{number}",
            name=f"job-{number}",
            created_at=NOW - timedelta(days=10),
            state=ContainerState.STOPPED,
            image_id="image-1",
        )
        for number in (1, 2)
    )
    plan = CleanupPlan(
        generated_at=NOW,
        decisions=tuple(
            CleanupDecision(
                resource_type="container",
                resource_id=container.id,
                resource_name=container.name,
                status="candidate",
                reasons=("old",),
            )
            for container in containers
        ),
    )
    gateway = FakeDockerGateway(fail_removals={"container-1"})

    result = CleanupExecutor(gateway, CleanupPolicy(), clock=lambda: NOW).execute(
        plan, Inventory(collected_at=NOW, containers=containers)
    )

    assert result.failed == 1
    assert result.succeeded == 1
    assert gateway.removed == [(containers[1].resource_type, "container-2")]


def test_interruption_stops_scheduling_new_deletions() -> None:
    container = ContainerResource(
        id="container-1",
        name="job",
        created_at=NOW - timedelta(days=10),
        state=ContainerState.STOPPED,
        image_id="image-1",
    )
    gateway = FakeDockerGateway()

    result = CleanupExecutor(
        gateway,
        CleanupPolicy(),
        clock=lambda: NOW,
        should_stop=lambda: True,
    ).execute(_candidate_plan(), Inventory(collected_at=NOW, containers=(container,)))

    assert result.interrupted
    assert result.items == ()
    assert gateway.removed == []


def test_signal_interruption_is_cooperative() -> None:
    interruption = SignalInterruption()

    assert not interruption.requested()
    interruption.request()
    assert interruption.requested()
