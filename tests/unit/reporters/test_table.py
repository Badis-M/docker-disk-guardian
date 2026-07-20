from datetime import UTC, datetime

from docker_disk_guardian.models import ImageResource, Inventory
from docker_disk_guardian.reporters.table import format_bytes, render_inventory


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

