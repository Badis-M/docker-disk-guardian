from unittest.mock import Mock, patch

import pytest
from docker.errors import DockerException

from docker_disk_guardian.docker_client import DockerSdkGateway
from docker_disk_guardian.errors import DockerUnavailableError


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

