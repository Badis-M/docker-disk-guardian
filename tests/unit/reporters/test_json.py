import json
from datetime import UTC, datetime

from docker_disk_guardian.models import CleanupDecision, CleanupPlan, ImageResource, Inventory
from docker_disk_guardian.reporters.json import render_inventory, render_plan


def test_json_inventory_has_versioned_contract() -> None:
    now = datetime(2026, 3, 7, tzinfo=UTC)
    inventory = Inventory(
        collected_at=now,
        images=(ImageResource(id="image-1", name="example:1", created_at=now, size_bytes=128),),
    )

    document = json.loads(render_inventory(inventory))

    assert document["schema_version"] == 1
    assert document["kind"] == "inventory"
    assert document["known_total_bytes"] == 128
    assert document["resources"]["images"][0]["id"] == "image-1"


def test_json_plan_has_candidate_summary() -> None:
    now = datetime(2026, 3, 7, tzinfo=UTC)
    plan = CleanupPlan(
        generated_at=now,
        decisions=(
            CleanupDecision(
                resource_type="image",
                resource_id="image-1",
                resource_name="dangling",
                status="candidate",
                reasons=("unused",),
                estimated_bytes=512,
            ),
        ),
    )

    document = json.loads(render_plan(plan))

    assert document["kind"] == "cleanup_plan"
    assert document["candidate_count"] == 1
    assert document["estimated_reclaimable_bytes"] == 512
