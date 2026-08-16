from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from docker_disk_guardian.models import (
    CleanupDecision,
    CleanupPlan,
    ContainerResource,
    ContainerState,
    DecisionStatus,
    ExecutionItem,
    ExecutionResult,
    ImageResource,
    Inventory,
)


def test_inventory_sums_only_known_sizes() -> None:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    container = ContainerResource(
        id="container-1",
        name="web",
        created_at=created_at,
        size_bytes=512,
        state=ContainerState.RUNNING,
        image_id="image-1",
    )
    image = ImageResource(
        id="image-1",
        name="example:1",
        created_at=created_at,
        size_bytes=None,
        tags=("example:1",),
    )

    inventory = Inventory(collected_at=created_at, containers=(container,), images=(image,))

    assert inventory.total_known_bytes == 512


def test_resource_rejects_naive_datetime() -> None:
    with pytest.raises(ValidationError, match="timezone information"):
        ImageResource(
            id="image-1",
            name="example:1",
            created_at=datetime(2026, 1, 1),
        )


def test_dangling_image_has_no_usable_tag() -> None:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)

    assert ImageResource(id="one", name="one", created_at=created_at).dangling
    assert ImageResource(
        id="two", name="two", created_at=created_at, tags=("<none>:<none>",)
    ).dangling
    assert not ImageResource(
        id="three", name="three", created_at=created_at, tags=("example:1",)
    ).dangling


def test_plan_sums_candidate_estimates_only() -> None:
    generated_at = datetime(2026, 4, 1, tzinfo=UTC)
    plan = CleanupPlan(
        generated_at=generated_at,
        decisions=(
            CleanupDecision(
                resource_type="image",
                resource_id="image-1",
                resource_name="one",
                status=DecisionStatus.CANDIDATE,
                reasons=("unused",),
                estimated_bytes=100,
            ),
            CleanupDecision(
                resource_type="image",
                resource_id="image-2",
                resource_name="two",
                status=DecisionStatus.PROTECTED,
                reasons=("in use",),
                estimated_bytes=200,
            ),
        ),
    )

    assert len(plan.candidates) == 1
    assert plan.estimated_reclaimable_bytes == 100


def test_execution_result_counts_each_outcome() -> None:
    now = datetime(2026, 4, 1, tzinfo=UTC)
    result = ExecutionResult(
        started_at=now,
        completed_at=now,
        items=(
            ExecutionItem(
                resource_type="image",
                resource_id="one",
                resource_name="one",
                status="succeeded",
                message="removed",
            ),
            ExecutionItem(
                resource_type="image",
                resource_id="two",
                resource_name="two",
                status="failed",
                message="daemon error",
            ),
            ExecutionItem(
                resource_type="build_cache",
                resource_id="three",
                resource_name="three",
                status="skipped",
                message="unsupported",
            ),
        ),
    )

    assert (result.succeeded, result.failed, result.skipped) == (1, 1, 1)
