"""Read-only orchestration for collecting Docker inventory."""

from collections.abc import Callable, Iterable
from datetime import UTC, datetime

from docker_disk_guardian.models import Inventory, ResourceType
from docker_disk_guardian.ports import DockerGateway

ALL_RESOURCE_TYPES = frozenset(ResourceType)


class InventoryService:
    def __init__(
        self,
        gateway: DockerGateway,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._gateway = gateway
        self._clock = clock or (lambda: datetime.now(UTC))

    def collect(self, include: Iterable[ResourceType] | None = None) -> Inventory:
        """Collect selected resources without mutating the daemon."""
        selected = set(include) if include is not None else set(ALL_RESOURCE_TYPES)
        return Inventory(
            collected_at=self._clock(),
            containers=(
                self._gateway.list_containers() if ResourceType.CONTAINER in selected else ()
            ),
            images=self._gateway.list_images() if ResourceType.IMAGE in selected else (),
            volumes=self._gateway.list_volumes() if ResourceType.VOLUME in selected else (),
            networks=self._gateway.list_networks() if ResourceType.NETWORK in selected else (),
            build_cache=(
                self._gateway.list_build_cache() if ResourceType.BUILD_CACHE in selected else ()
            ),
        )

