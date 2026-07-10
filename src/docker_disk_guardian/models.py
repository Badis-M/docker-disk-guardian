"""Typed domain models independent from Docker SDK responses."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResourceType(StrEnum):
    CONTAINER = "container"
    IMAGE = "image"
    VOLUME = "volume"
    NETWORK = "network"
    BUILD_CACHE = "build_cache"


class ContainerState(StrEnum):
    RUNNING = "running"
    STOPPED = "stopped"
    OTHER = "other"


class DomainModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Resource(DomainModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    created_at: datetime
    size_bytes: int | None = Field(default=None, ge=0)
    labels: dict[str, str] = Field(default_factory=dict)

    @field_validator("created_at")
    @classmethod
    def require_aware_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must include timezone information")
        return value.astimezone(UTC)


class ContainerResource(Resource):
    resource_type: ResourceType = ResourceType.CONTAINER
    state: ContainerState
    image_id: str
    finished_at: datetime | None = None
    volume_names: tuple[str, ...] = ()
    network_names: tuple[str, ...] = ()

    @field_validator("finished_at")
    @classmethod
    def normalize_optional_datetime(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("finished_at must include timezone information")
        return value.astimezone(UTC)


class ImageResource(Resource):
    resource_type: ResourceType = ResourceType.IMAGE
    tags: tuple[str, ...] = ()
    digests: tuple[str, ...] = ()
    container_ids: tuple[str, ...] = ()

    @property
    def dangling(self) -> bool:
        return not self.tags or self.tags == ("<none>:<none>",)


class VolumeResource(Resource):
    resource_type: ResourceType = ResourceType.VOLUME
    driver: str = "local"
    container_ids: tuple[str, ...] = ()
    anonymous: bool = False


class NetworkResource(Resource):
    resource_type: ResourceType = ResourceType.NETWORK
    driver: str = "bridge"
    container_ids: tuple[str, ...] = ()
    default: bool = False


class BuildCacheResource(Resource):
    resource_type: ResourceType = ResourceType.BUILD_CACHE
    cache_type: str = "regular"
    in_use: bool = False


class Inventory(DomainModel):
    collected_at: datetime
    containers: tuple[ContainerResource, ...] = ()
    images: tuple[ImageResource, ...] = ()
    volumes: tuple[VolumeResource, ...] = ()
    networks: tuple[NetworkResource, ...] = ()
    build_cache: tuple[BuildCacheResource, ...] = ()

    @field_validator("collected_at")
    @classmethod
    def normalize_collected_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("collected_at must include timezone information")
        return value.astimezone(UTC)

    @property
    def total_known_bytes(self) -> int:
        resources: tuple[Resource, ...] = (
            *self.containers,
            *self.images,
            *self.volumes,
            *self.networks,
            *self.build_cache,
        )
        return sum(resource.size_bytes or 0 for resource in resources)

