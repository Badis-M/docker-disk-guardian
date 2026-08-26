"""Application ports implemented by external system adapters."""

from typing import Protocol

from docker_disk_guardian.models import (
    BuildCacheResource,
    ContainerResource,
    ImageResource,
    NetworkResource,
    ResourceType,
    VolumeResource,
)


class DockerGateway(Protocol):
    """Typed boundary for all Docker daemon interactions."""

    def list_containers(self) -> tuple[ContainerResource, ...]: ...

    def list_images(self) -> tuple[ImageResource, ...]: ...

    def list_volumes(self) -> tuple[VolumeResource, ...]: ...

    def list_networks(self) -> tuple[NetworkResource, ...]: ...

    def list_build_cache(self) -> tuple[BuildCacheResource, ...]: ...

    def remove(self, resource_type: ResourceType, resource_id: str) -> None: ...

    def close(self) -> None: ...
