from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from docker_disk_guardian.models import (
    ContainerResource,
    ContainerState,
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

