"""Docker SDK adapter for the typed application gateway."""

from __future__ import annotations

from typing import Any

import docker
from docker.client import DockerClient
from docker.errors import DockerException

from docker_disk_guardian.errors import DockerUnavailableError
from docker_disk_guardian.models import (
    BuildCacheResource,
    ContainerResource,
    ImageResource,
    NetworkResource,
    ResourceType,
    VolumeResource,
)


class DockerSdkGateway:
    """Translate Docker SDK objects into stable domain models."""

    def __init__(self, client: DockerClient) -> None:
        self._client = client

    @classmethod
    def connect(cls) -> DockerSdkGateway:
        """Connect using Docker's standard environment and socket discovery."""
        try:
            client = docker.from_env()
            client.ping()
        except DockerException as exc:
            raise DockerUnavailableError(
                "Cannot connect to Docker. Start the daemon and verify access to the Docker socket."
            ) from exc
        return cls(client)

    def list_containers(self) -> tuple[ContainerResource, ...]:
        raise NotImplementedError

    def list_images(self) -> tuple[ImageResource, ...]:
        raise NotImplementedError

    def list_volumes(self) -> tuple[VolumeResource, ...]:
        raise NotImplementedError

    def list_networks(self) -> tuple[NetworkResource, ...]:
        raise NotImplementedError

    def list_build_cache(self) -> tuple[BuildCacheResource, ...]:
        raise NotImplementedError

    def remove(self, resource_type: ResourceType, resource_id: str) -> None:
        removers: dict[ResourceType, Any] = {
            ResourceType.CONTAINER: self._client.containers.get(resource_id).remove,
            ResourceType.IMAGE: lambda: self._client.images.remove(resource_id),
            ResourceType.VOLUME: self._client.volumes.get(resource_id).remove,
            ResourceType.NETWORK: self._client.networks.get(resource_id).remove,
        }
        try:
            remover = removers[resource_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported removal type: {resource_type}") from exc
        remover()

    def close(self) -> None:
        self._client.close()

