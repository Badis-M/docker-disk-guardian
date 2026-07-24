"""Strict cleanup policy models and duration parsing."""

import re
from datetime import timedelta
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

_DURATION_PATTERN = re.compile(r"^(?P<amount>[1-9][0-9]*)(?P<unit>[smhdw])$")
_DURATION_FACTORS = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 24 * 60 * 60,
    "w": 7 * 24 * 60 * 60,
}


def parse_duration(value: object) -> timedelta:
    if isinstance(value, timedelta):
        if value <= timedelta(0):
            raise ValueError("duration must be positive")
        return value
    if not isinstance(value, str):
        raise ValueError("duration must use a value such as '72h' or '7d'")
    match = _DURATION_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError("duration must be a positive integer followed by s, m, h, d, or w")
    seconds = int(match.group("amount")) * _DURATION_FACTORS[match.group("unit")]
    return timedelta(seconds=seconds)


Duration = Annotated[timedelta, BeforeValidator(parse_duration)]


class PolicyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RetentionPolicy(PolicyModel):
    stopped_containers: Duration = timedelta(hours=168)
    dangling_images: Duration = timedelta(hours=72)
    build_cache: Duration = timedelta(hours=168)


class ProtectionPolicy(PolicyModel):
    labels: dict[str, str] = Field(default_factory=lambda: {"keep": "true"})
    image_tags: tuple[str, ...] = ("latest",)


class VolumePolicy(PolicyModel):
    allow_named_volume_deletion: bool = False


class NetworkPolicy(PolicyModel):
    allow_custom_network_deletion: bool = False


class BuildCachePolicy(PolicyModel):
    allow_deletion: bool = False


class CleanupPolicy(PolicyModel):
    version: Literal[1] = 1
    retention: RetentionPolicy = Field(default_factory=RetentionPolicy)
    protection: ProtectionPolicy = Field(default_factory=ProtectionPolicy)
    volumes: VolumePolicy = Field(default_factory=VolumePolicy)
    networks: NetworkPolicy = Field(default_factory=NetworkPolicy)
    build_cache: BuildCachePolicy = Field(default_factory=BuildCachePolicy)

