from datetime import UTC, datetime

from docker_disk_guardian.inventory import InventoryService
from docker_disk_guardian.models import ImageResource, ResourceType
from tests.fakes import FakeDockerGateway


def test_collects_only_selected_resource_types() -> None:
    now = datetime(2026, 3, 7, tzinfo=UTC)
    image = ImageResource(id="image-1", name="example:1", created_at=now)
    gateway = FakeDockerGateway(images=(image,))

    inventory = InventoryService(gateway, clock=lambda: now).collect([ResourceType.IMAGE])

    assert inventory.images == (image,)
    assert inventory.containers == ()
    assert inventory.collected_at == now


def test_collection_never_calls_remove() -> None:
    gateway = FakeDockerGateway()

    InventoryService(gateway).collect()

    assert gateway.removed == []
