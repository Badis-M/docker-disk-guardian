"""Docker SDK adapter for the typed application gateway."""

from __future__ import annotations

from datetime import UTC, datetime
import re
from typing import Any

import docker
from docker.client import DockerClient
from docker.errors import APIError, DockerException

from docker_disk_guardian.errors import DockerUnavailableError
from docker_disk_guardian.models import (
    BuildCacheResource,
    ContainerResource,
    ContainerState,
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
        resources: list[ContainerResource] = []
        for summary in self._client.api.containers(all=True):
            details = self._client.api.inspect_container(summary["Id"], size=True)
            state_data = details.get("State", {})
            status = state_data.get("Status", summary.get("State", "unknown"))
            mounts = details.get("Mounts", [])
            networks = details.get("NetworkSettings", {}).get("Networks", {})
            names = summary.get("Names") or [details.get("Name", summary["Id"][:12])]
            resources.append(
                ContainerResource(
                    id=summary["Id"],
                    name=str(names[0]).lstrip("/"),
                    created_at=self._parse_datetime(details.get("Created", summary["Created"])),
                    size_bytes=details.get("SizeRw"),
                    labels=details.get("Config", {}).get("Labels") or summary.get("Labels") or {},
                    state=self._container_state(status),
                    image_id=details.get("Image", summary.get("ImageID", "unknown")),
                    finished_at=self._optional_datetime(state_data.get("FinishedAt")),
                    volume_names=tuple(
                        sorted(
                            mount["Name"]
                            for mount in mounts
                            if mount.get("Type") == "volume" and mount.get("Name")
                        )
                    ),
                    network_names=tuple(sorted(networks)),
                )
            )
        return tuple(resources)

    def list_images(self) -> tuple[ImageResource, ...]:
        references: dict[str, list[str]] = {}
        for container in self._client.api.containers(all=True):
            references.setdefault(container.get("ImageID", ""), []).append(container["Id"])

        resources: list[ImageResource] = []
        for image in self._client.images.list(all=True):
            attributes = image.attrs
            tags = tuple(sorted(attributes.get("RepoTags") or ()))
            resources.append(
                ImageResource(
                    id=image.id,
                    name=tags[0] if tags else image.short_id,
                    created_at=self._parse_datetime(attributes["Created"]),
                    size_bytes=attributes.get("Size"),
                    labels=attributes.get("Config", {}).get("Labels") or {},
                    tags=tags,
                    digests=tuple(sorted(attributes.get("RepoDigests") or ())),
                    container_ids=tuple(sorted(references.get(image.id, ()))),
                )
            )
        return tuple(resources)

    def list_volumes(self) -> tuple[VolumeResource, ...]:
        references: dict[str, list[str]] = {}
        for container in self._client.api.containers(all=True):
            for mount in container.get("Mounts") or ():
                if mount.get("Type") == "volume" and mount.get("Name"):
                    references.setdefault(mount["Name"], []).append(container["Id"])

        resources: list[VolumeResource] = []
        for volume in self._client.volumes.list():
            attributes = volume.attrs
            name = attributes.get("Name", volume.name)
            raw_size = (attributes.get("UsageData") or {}).get("Size")
            size = raw_size if isinstance(raw_size, int) and raw_size >= 0 else None
            resources.append(
                VolumeResource(
                    id=name,
                    name=name,
                    created_at=self._parse_datetime(
                        attributes.get("CreatedAt", "1970-01-01T00:00:00Z")
                    ),
                    size_bytes=size,
                    labels=attributes.get("Labels") or {},
                    driver=attributes.get("Driver", "unknown"),
                    container_ids=tuple(sorted(references.get(name, ()))),
                    anonymous=re.fullmatch(r"[a-f0-9]{64}", name) is not None,
                )
            )
        return tuple(resources)

    def list_networks(self) -> tuple[NetworkResource, ...]:
        resources: list[NetworkResource] = []
        for network in self._client.networks.list():
            attributes = network.attrs
            name = attributes.get("Name", network.name)
            resources.append(
                NetworkResource(
                    id=attributes.get("Id", network.id),
                    name=name,
                    created_at=self._parse_datetime(
                        attributes.get("Created", "1970-01-01T00:00:00Z")
                    ),
                    labels=attributes.get("Labels") or {},
                    driver=attributes.get("Driver", "unknown"),
                    container_ids=tuple(sorted((attributes.get("Containers") or {}).keys())),
                    default=name in {"bridge", "host", "none"},
                )
            )
        return tuple(resources)

    def list_build_cache(self) -> tuple[BuildCacheResource, ...]:
        try:
            cache_entries = self._client.api.df().get("BuildCache") or ()
        except APIError as exc:
            if exc.status_code in {400, 404}:
                return ()
            raise
        return tuple(
            BuildCacheResource(
                id=entry["ID"],
                name=entry.get("Description") or entry["ID"][:12],
                created_at=self._parse_datetime(entry["CreatedAt"]),
                size_bytes=max(0, entry.get("Size", 0)),
                cache_type=entry.get("Type", "unknown"),
                in_use=entry.get("InUse", False),
            )
            for entry in cache_entries
        )

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

    @staticmethod
    def _parse_datetime(value: str | int | float) -> datetime:
        if isinstance(value, int | float):
            return datetime.fromtimestamp(value, tz=UTC)
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).astimezone(UTC)

    @classmethod
    def _optional_datetime(cls, value: object) -> datetime | None:
        if not isinstance(value, str) or not value or value.startswith("0001-"):
            return None
        return cls._parse_datetime(value)

    @staticmethod
    def _container_state(value: str) -> ContainerState:
        if value == "running":
            return ContainerState.RUNNING
        if value in {"exited", "dead"}:
            return ContainerState.STOPPED
        return ContainerState.OTHER
