"""Smoke-test an installed distribution without Docker, cloud, or host inspection."""

import importlib
import importlib.metadata
import json
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "docker_disk_guardian"
NAME = "docker-disk-guardian"


def main() -> None:
    expected = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    assert importlib.metadata.version(NAME) == expected
    module = importlib.import_module(PACKAGE)
    assert module.__file__ is not None
    assert ROOT / "src" not in Path(module.__file__).resolve().parents, (
        "source checkout masks installed wheel"
    )
    with tempfile.TemporaryDirectory(prefix="distribution-smoke-") as directory:
        work = Path(directory)
        if NAME == "ai-cloud-audit":
            fixture = work / "fixture"
            fixture.mkdir()
            (fixture / "Dockerfile").write_text("FROM ubuntu:latest\n")
            report = work / "report.json"
            subprocess.run(
                [sys.executable, "-m", PACKAGE, "scan", str(fixture), "--output", str(report)],
                check=True,
                cwd=work,
            )
            payload = json.loads(report.read_text())
            assert payload["schema_version"] == "1.0"
            assert payload["tool"]["version"] == expected
            assert payload["status"] == "complete"
            assert any(item["rule_id"] == "DOCKER001" for item in payload["findings"])
            from importlib.resources import files

            assert files(PACKAGE).joinpath("schemas/report-1.0.schema.json").is_file()
        else:
            result = subprocess.run(
                [sys.executable, "-m", PACKAGE + ".cli", "version", "--short"],
                check=True,
                capture_output=True,
                text=True,
                cwd=work,
            )
            assert result.stdout.strip() == expected
            policy = work / "policy.yaml"
            policy.write_text("version: 1\n")
            subprocess.run(
                [sys.executable, "-m", PACKAGE + ".cli", "policy", "validate", str(policy)],
                check=True,
                cwd=work,
            )
    print("Installed distribution smoke test passed")


if __name__ == "__main__":
    main()
