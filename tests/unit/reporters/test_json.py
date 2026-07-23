import json
from datetime import UTC, datetime

from docker_disk_guardian.models import ImageResource, Inventory
from docker_disk_guardian.reporters.json import render_inventory


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

