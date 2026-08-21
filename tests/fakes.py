from dataclasses import dataclass, field

from docker_disk_guardian.models import (
    BuildCacheResource,
    ContainerResource,
    ImageResource,
    NetworkResource,
    ResourceType,
    VolumeResource,
)


@dataclass
class FakeDockerGateway:
    containers: tuple[ContainerResource, ...] = ()
    images: tuple[ImageResource, ...] = ()
    volumes: tuple[VolumeResource, ...] = ()
    networks: tuple[NetworkResource, ...] = ()
    build_cache: tuple[BuildCacheResource, ...] = ()
    removed: list[tuple[ResourceType, str]] = field(default_factory=list)
    fail_removals: set[str] = field(default_factory=set)
    closed: bool = False

    def list_containers(self) -> tuple[ContainerResource, ...]:
        return self.containers

    def list_images(self) -> tuple[ImageResource, ...]:
        return self.images

    def list_volumes(self) -> tuple[VolumeResource, ...]:
        return self.volumes

    def list_networks(self) -> tuple[NetworkResource, ...]:
        return self.networks

    def list_build_cache(self) -> tuple[BuildCacheResource, ...]:
        return self.build_cache

    def remove(self, resource_type: ResourceType, resource_id: str) -> None:
        if resource_id in self.fail_removals:
            raise RuntimeError(f"cannot remove {resource_id}")
        self.removed.append((resource_type, resource_id))

    def close(self) -> None:
        self.closed = True
