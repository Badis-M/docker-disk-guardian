from unittest.mock import Mock, patch

import pytest
from docker.errors import DockerException

from docker_disk_guardian.docker_client import DockerSdkGateway
from docker_disk_guardian.errors import DockerUnavailableError
from docker_disk_guardian.models import ContainerState


@patch("docker_disk_guardian.docker_client.docker.from_env")
def test_connect_pings_daemon(from_env: Mock) -> None:
    client = from_env.return_value

    gateway = DockerSdkGateway.connect()

    client.ping.assert_called_once_with()
    gateway.close()
    client.close.assert_called_once_with()


@patch("docker_disk_guardian.docker_client.docker.from_env")
def test_connection_failure_is_actionable(from_env: Mock) -> None:
    from_env.side_effect = DockerException("socket unavailable")

    with pytest.raises(DockerUnavailableError, match="Start the daemon"):
        DockerSdkGateway.connect()


def test_lists_typed_containers() -> None:
    client = Mock()
    client.api.containers.return_value = [
        {
            "Id": "container-1",
            "Names": ["/web"],
            "Created": 1_772_841_600,
            "ImageID": "image-1",
            "State": "exited",
            "Labels": {},
        }
    ]
    client.api.inspect_container.return_value = {
        "Id": "container-1",
        "Name": "/web",
        "Created": "2026-03-07T00:00:00Z",
        "Image": "image-1",
        "SizeRw": 1024,
        "Config": {"Labels": {"purpose": "test"}},
        "State": {"Status": "exited", "FinishedAt": "2026-03-08T00:00:00Z"},
        "Mounts": [{"Type": "volume", "Name": "web-data"}],
        "NetworkSettings": {"Networks": {"frontend": {}}},
    }

    containers = DockerSdkGateway(client).list_containers()

    assert len(containers) == 1
    assert containers[0].name == "web"
    assert containers[0].state == ContainerState.STOPPED
    assert containers[0].size_bytes == 1024
    assert containers[0].volume_names == ("web-data",)
    assert containers[0].network_names == ("frontend",)
    client.api.inspect_container.assert_called_once_with("container-1")


def test_lists_images_with_container_references() -> None:
    client = Mock()
    client.api.containers.return_value = [{"Id": "container-1", "ImageID": "sha256:image-1"}]
    image = Mock()
    image.id = "sha256:image-1"
    image.short_id = "sha256:image"
    image.attrs = {
        "Created": "2026-03-07T00:00:00Z",
        "Size": 2048,
        "RepoTags": ["example:1"],
        "RepoDigests": ["example@sha256:digest"],
        "Config": {"Labels": {"keep": "true"}},
    }
    client.images.list.return_value = [image]

    images = DockerSdkGateway(client).list_images()

    assert images[0].name == "example:1"
    assert images[0].container_ids == ("container-1",)
    assert images[0].labels == {"keep": "true"}


def test_lists_volumes_and_preserves_named_volume_safety_context() -> None:
    client = Mock()
    client.api.containers.return_value = [
        {
            "Id": "container-1",
            "Mounts": [{"Type": "volume", "Name": "database-data"}],
        }
    ]
    volume = Mock()
    volume.name = "database-data"
    volume.attrs = {
        "Name": "database-data",
        "CreatedAt": "2026-03-07T00:00:00Z",
        "Driver": "local",
        "Labels": {},
        "UsageData": {"Size": 4096},
    }
    client.volumes.list.return_value = [volume]

    volumes = DockerSdkGateway(client).list_volumes()

    assert volumes[0].container_ids == ("container-1",)
    assert volumes[0].size_bytes == 4096
    assert not volumes[0].anonymous


def test_marks_default_networks_as_protected_context() -> None:
    client = Mock()
    network = Mock()
    network.id = "network-1"
    network.name = "bridge"
    network.attrs = {
        "Id": "network-1",
        "Name": "bridge",
        "Created": "2026-03-07T00:00:00Z",
        "Driver": "bridge",
        "Labels": {},
        "Containers": {},
    }
    client.networks.list.return_value = [network]

    networks = DockerSdkGateway(client).list_networks()

    assert networks[0].default
    assert networks[0].container_ids == ()


def test_lists_build_cache_when_api_supports_disk_usage() -> None:
    client = Mock()
    client.api.df.return_value = {
        "BuildCache": [
            {
                "ID": "cache-123456789",
                "Type": "regular",
                "Description": "pip layer",
                "CreatedAt": 1_772_841_600,
                "Size": 8192,
                "InUse": False,
            }
        ]
    }

    cache = DockerSdkGateway(client).list_build_cache()

    assert cache[0].name == "pip layer"
    assert cache[0].size_bytes == 8192
    assert not cache[0].in_use
