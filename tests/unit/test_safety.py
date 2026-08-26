from datetime import UTC, datetime

from docker_disk_guardian.config import CleanupPolicy
from docker_disk_guardian.models import (
    ContainerResource,
    ContainerState,
    ImageResource,
    NetworkResource,
    VolumeResource,
)
from docker_disk_guardian.safety import protection_reasons

NOW = datetime(2026, 4, 1, tzinfo=UTC)


def test_running_container_is_always_protected() -> None:
    container = ContainerResource(
        id="container-1",
        name="web",
        created_at=NOW,
        state=ContainerState.RUNNING,
        image_id="image-1",
    )

    assert "container is running" in protection_reasons(container, CleanupPolicy())


def test_referenced_image_and_latest_tag_are_protected() -> None:
    image = ImageResource(
        id="image-1",
        name="example:latest",
        created_at=NOW,
        tags=("example:latest",),
        container_ids=("container-1",),
    )

    reasons = protection_reasons(image, CleanupPolicy())

    assert "image is referenced by an existing container" in reasons
    assert "image tag matches a protected pattern" in reasons


def test_named_volume_is_protected_by_default() -> None:
    volume = VolumeResource(id="data", name="data", created_at=NOW)

    assert "named volume deletion is disabled by policy" in protection_reasons(
        volume, CleanupPolicy()
    )


def test_default_network_cannot_be_unprotected_by_policy() -> None:
    network = NetworkResource(id="bridge", name="bridge", created_at=NOW, default=True)
    policy = CleanupPolicy.model_validate({"networks": {"allow_custom_network_deletion": True}})

    assert "Docker default network is always protected" in protection_reasons(network, policy)
