from datetime import UTC, datetime

from docker_disk_guardian.models import CleanupDecision, CleanupPlan, ImageResource, Inventory
from docker_disk_guardian.reporters.markdown import render_inventory, render_plan


def test_markdown_inventory_escapes_table_content() -> None:
    now = datetime(2026, 3, 7, tzinfo=UTC)
    inventory = Inventory(
        collected_at=now,
        images=(ImageResource(id="image-1", name="repo|unsafe", created_at=now),),
    )

    report = render_inventory(inventory)

    assert "repo\\|unsafe" in report
    assert "# Docker Disk Inventory" in report


def test_markdown_plan_contains_reasons() -> None:
    now = datetime(2026, 3, 7, tzinfo=UTC)
    plan = CleanupPlan(
        generated_at=now,
        decisions=(
            CleanupDecision(
                resource_type="container",
                resource_id="container-1",
                resource_name="job",
                status="protected",
                reasons=("container is running",),
            ),
        ),
    )

    report = render_plan(plan)

    assert "container is running" in report
    assert "Candidates: **0**" in report

