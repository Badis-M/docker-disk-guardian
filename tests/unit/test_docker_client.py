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
    client.api.inspect_container.assert_called_once_with("container-1", size=True)
