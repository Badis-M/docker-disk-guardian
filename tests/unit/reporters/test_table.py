from datetime import UTC, datetime

from docker_disk_guardian.models import CleanupDecision, CleanupPlan, ImageResource, Inventory
from docker_disk_guardian.reporters.table import format_bytes, render_inventory, render_plan


def test_formats_binary_sizes() -> None:
    assert format_bytes(None) == "unknown"
    assert format_bytes(512) == "512 B"
    assert format_bytes(1536) == "1.5 KiB"


def test_renders_stable_inventory_table() -> None:
    now = datetime(2026, 3, 7, tzinfo=UTC)
    inventory = Inventory(
        collected_at=now,
        images=(ImageResource(id="image-123456789", name="example:1", created_at=now, size_bytes=1024),),
    )

    report = render_inventory(inventory, color=False)

    assert "Docker Disk Inventory" in report
    assert "example:1" in report
    assert "1.0 KiB" in report
    assert "Known total: 1.0 KiB" in report


def test_renders_explainable_plan_table() -> None:
    now = datetime(2026, 3, 7, tzinfo=UTC)
    plan = CleanupPlan(
        generated_at=now,
        decisions=(
            CleanupDecision(
                resource_type="image",
                resource_id="image-1",
                resource_name="dangling",
                status="candidate",
                reasons=("dangling image exceeds retention",),
                estimated_bytes=1024,
            ),
        ),
    )

    report = render_plan(plan, color=False)

    assert "Docker Cleanup Plan" in report
    assert "dangling image exceeds retention" in report
    assert "Candidates: 1" in report
