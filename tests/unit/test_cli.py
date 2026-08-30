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
    assert result.stdout == "docker-disk-guardian 1.0.0\n"


def test_short_version_command() -> None:
    result = runner.invoke(app, ["version", "--short"])

    assert result.exit_code == 0
    assert result.stdout == "1.0.0\n"


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


def test_policy_validate_does_not_connect_to_docker(tmp_path: object) -> None:
    from pathlib import Path

    policy = Path(str(tmp_path)) / "policy.yaml"
    policy.write_text("version: 1\n", encoding="utf-8")

    with patch("docker_disk_guardian.cli.DockerSdkGateway.connect") as connect:
        result = runner.invoke(app, ["policy", "validate", str(policy)])

    assert result.exit_code == 0
    assert result.stdout == "Policy is valid (version 1).\n"
    connect.assert_not_called()


@patch("docker_disk_guardian.cli.DockerSdkGateway.connect")
def test_plan_is_read_only_and_explains_decisions(connect: object) -> None:
    gateway = FakeDockerGateway(
        images=(
            ImageResource(
                id="image-1",
                name="dangling",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
                size_bytes=1024,
            ),
        )
    )
    connect.return_value = gateway  # type: ignore[attr-defined]

    result = runner.invoke(app, ["plan", "--format", "json"])

    assert result.exit_code == 0
    assert '"kind": "cleanup_plan"' in result.stdout
    assert '"status": "candidate"' in result.stdout
    assert gateway.removed == []
    assert gateway.closed


@patch("docker_disk_guardian.cli.DockerSdkGateway.connect")
def test_apply_requires_confirmation(connect: object, tmp_path: object) -> None:
    from pathlib import Path

    policy_path = Path(str(tmp_path)) / "policy.yaml"
    policy_path.write_text("version: 1\n", encoding="utf-8")
    gateway = FakeDockerGateway(
        images=(
            ImageResource(
                id="image-1",
                name="dangling",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
        )
    )
    connect.return_value = gateway  # type: ignore[attr-defined]

    result = runner.invoke(app, ["apply", "--policy", str(policy_path)], input="n\n")

    assert result.exit_code == 1
    assert gateway.removed == []
    assert gateway.closed


@patch("docker_disk_guardian.cli.DockerSdkGateway.connect")
def test_apply_yes_removes_only_planned_candidate(connect: object, tmp_path: object) -> None:
    from pathlib import Path

    policy_path = Path(str(tmp_path)) / "policy.yaml"
    policy_path.write_text("version: 1\n", encoding="utf-8")
    gateway = FakeDockerGateway(
        images=(
            ImageResource(
                id="image-1",
                name="dangling",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
        )
    )
    connect.return_value = gateway  # type: ignore[attr-defined]

    result = runner.invoke(
        app,
        ["apply", "--policy", str(policy_path), "--yes"],
    )

    assert result.exit_code == 0
    assert gateway.removed == [(gateway.images[0].resource_type, "image-1")]
    assert "Execution summary: 1 succeeded" in result.stdout
