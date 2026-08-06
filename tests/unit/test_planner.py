from datetime import UTC, datetime, timedelta

from docker_disk_guardian.config import CleanupPolicy
from docker_disk_guardian.models import (
    ContainerResource,
    ContainerState,
    DecisionStatus,
    ImageResource,
    Inventory,
)
from docker_disk_guardian.planner import CleanupPlanner

NOW = datetime(2026, 4, 14, tzinfo=UTC)


def test_old_stopped_container_becomes_candidate() -> None:
    container = ContainerResource(
        id="container-1",
        name="old-job",
        created_at=NOW - timedelta(days=10),
        finished_at=NOW - timedelta(days=8),
        state=ContainerState.STOPPED,
        image_id="image-1",
        size_bytes=1024,
    )
    inventory = Inventory(collected_at=NOW, containers=(container,))

    plan = CleanupPlanner(CleanupPolicy(), clock=lambda: NOW).create_plan(inventory)

    assert plan.decisions[0].status == DecisionStatus.CANDIDATE
    assert plan.estimated_reclaimable_bytes == 1024


def test_recent_stopped_container_is_retained() -> None:
    container = ContainerResource(
        id="container-1",
        name="recent-job",
        created_at=NOW - timedelta(days=1),
        state=ContainerState.STOPPED,
        image_id="image-1",
    )

    plan = CleanupPlanner(CleanupPolicy(), clock=lambda: NOW).create_plan(
        Inventory(collected_at=NOW, containers=(container,))
    )

    assert plan.decisions[0].status == DecisionStatus.RETAINED


def test_old_unreferenced_dangling_image_becomes_candidate() -> None:
    image = ImageResource(
        id="image-1",
        name="sha256:image",
        created_at=NOW - timedelta(days=5),
        size_bytes=2048,
    )

    plan = CleanupPlanner(CleanupPolicy(), clock=lambda: NOW).create_plan(
        Inventory(collected_at=NOW, images=(image,))
    )

    assert plan.decisions[0].status == DecisionStatus.CANDIDATE


def test_labeled_candidate_is_protected() -> None:
    image = ImageResource(
        id="image-1",
        name="sha256:image",
        created_at=NOW - timedelta(days=30),
        labels={"keep": "true"},
    )

    plan = CleanupPlanner(CleanupPolicy(), clock=lambda: NOW).create_plan(
        Inventory(collected_at=NOW, images=(image,))
    )

    assert plan.decisions[0].status == DecisionStatus.PROTECTED
    assert "protected by label keep=true" in plan.decisions[0].reasons

