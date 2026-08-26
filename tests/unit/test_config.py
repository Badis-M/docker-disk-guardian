from datetime import timedelta

import pytest
from pydantic import ValidationError

from docker_disk_guardian.config import CleanupPolicy, load_policy, parse_duration
from docker_disk_guardian.errors import ConfigurationError


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("30m", timedelta(minutes=30)),
        ("72h", timedelta(hours=72)),
        ("7d", timedelta(days=7)),
        ("2w", timedelta(weeks=2)),
    ],
)
def test_parse_duration(raw: str, expected: timedelta) -> None:
    assert parse_duration(raw) == expected


@pytest.mark.parametrize("raw", ["0h", "-2d", "1.5h", "forever", 72])
def test_rejects_invalid_duration(raw: object) -> None:
    with pytest.raises(ValueError, match="duration"):
        parse_duration(raw)


def test_policy_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CleanupPolicy.model_validate({"version": 1, "aggressive": True})


def test_default_policy_protects_named_volumes_and_cache() -> None:
    policy = CleanupPolicy()

    assert not policy.volumes.allow_named_volume_deletion
    assert not policy.build_cache.allow_deletion


def test_loads_valid_yaml_policy(tmp_path: object) -> None:
    from pathlib import Path

    path = Path(str(tmp_path)) / "policy.yaml"
    path.write_text(
        "version: 1\nretention:\n  stopped_containers: 48h\n",
        encoding="utf-8",
    )

    policy = load_policy(path)

    assert policy.retention.stopped_containers == timedelta(hours=48)


def test_reports_field_path_for_invalid_policy(tmp_path: object) -> None:
    from pathlib import Path

    path = Path(str(tmp_path)) / "policy.yaml"
    path.write_text("retention:\n  stopped_containers: -2h\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match=r"retention\.stopped_containers"):
        load_policy(path)


def test_rejects_non_mapping_policy(tmp_path: object) -> None:
    from pathlib import Path

    path = Path(str(tmp_path)) / "policy.yaml"
    path.write_text("- unsafe\n- list\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="YAML mapping"):
        load_policy(path)
