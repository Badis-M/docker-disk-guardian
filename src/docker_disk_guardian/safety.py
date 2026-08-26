"""Non-bypassable resource protection rules."""

from fnmatch import fnmatch

from docker_disk_guardian.config import CleanupPolicy
from docker_disk_guardian.models import (
    BuildCacheResource,
    ContainerResource,
    ContainerState,
    ImageResource,
    NetworkResource,
    Resource,
    VolumeResource,
)


def protection_reasons(resource: Resource, policy: CleanupPolicy) -> tuple[str, ...]:
    """Return every reason that prevents a resource from becoming a candidate."""
    reasons: list[str] = []
    for key, expected in policy.protection.labels.items():
        if resource.labels.get(key) == expected:
            reasons.append(f"protected by label {key}={expected}")

    if isinstance(resource, ContainerResource) and resource.state == ContainerState.RUNNING:
        reasons.append("container is running")
    elif isinstance(resource, ImageResource):
        if resource.container_ids:
            reasons.append("image is referenced by an existing container")
        if any(_protected_tag(tag, policy.protection.image_tags) for tag in resource.tags):
            reasons.append("image tag matches a protected pattern")
    elif isinstance(resource, VolumeResource):
        if resource.container_ids:
            reasons.append("volume is referenced by an existing container")
        if not resource.anonymous and not policy.volumes.allow_named_volume_deletion:
            reasons.append("named volume deletion is disabled by policy")
    elif isinstance(resource, NetworkResource):
        if resource.default:
            reasons.append("Docker default network is always protected")
        if resource.container_ids:
            reasons.append("network is referenced by an existing container")
        if not resource.default and not policy.networks.allow_custom_network_deletion:
            reasons.append("custom network deletion is disabled by policy")
    elif isinstance(resource, BuildCacheResource):
        if resource.in_use:
            reasons.append("build cache entry is in use")
        if not policy.build_cache.allow_deletion:
            reasons.append("build cache deletion is disabled by policy")

    return tuple(reasons)


def _protected_tag(tag: str, patterns: tuple[str, ...]) -> bool:
    tag_name = tag.rsplit(":", maxsplit=1)[-1]
    return any(fnmatch(tag, pattern) or fnmatch(tag_name, pattern) for pattern in patterns)
