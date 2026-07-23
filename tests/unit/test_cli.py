from datetime import UTC, datetime
from unittest.mock import patch

from typer.testing import CliRunner

from docker_disk_guardian.cli import app
from docker_disk_guardian.models import ImageResource
from tests.fakes import FakeDockerGateway

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout == "docker-disk-guardian 0.1.0\n"


def test_short_version_command() -> None:
    result = runner.invoke(app, ["version", "--short"])

    assert result.exit_code == 0
    assert result.stdout == "0.1.0\n"


@patch("docker_disk_guardian.cli.DockerSdkGateway.connect")
def test_inspect_renders_json_without_removing_resources(connect: object) -> None:
    now = datetime(2026, 3, 7, tzinfo=UTC)
    gateway = FakeDockerGateway(
        images=(ImageResource(id="image-1", name="example:1", created_at=now),)
    )
    connect.return_value = gateway  # type: ignore[attr-defined]

    result = runner.invoke(app, ["inspect", "--include", "image", "--format", "json"])

    assert result.exit_code == 0
    assert '"kind": "inventory"' in result.stdout
    assert gateway.removed == []
    assert gateway.closed


def test_inspect_rejects_empty_selection() -> None:
    result = runner.invoke(
        app,
        [
            "inspect",
            "--exclude",
            "container",
            "--exclude",
            "image",
            "--exclude",
            "volume",
            "--exclude",
            "network",
            "--exclude",
            "build_cache",
        ],
    )

    assert result.exit_code == 2
    assert "At least one resource type" in result.output
