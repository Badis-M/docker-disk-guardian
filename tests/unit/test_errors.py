from docker_disk_guardian.errors import (
    ConfigurationError,
    DockerUnavailableError,
    ExecutionError,
    ExitCode,
)


def test_expected_errors_have_stable_exit_codes() -> None:
    assert ConfigurationError.exit_code == ExitCode.INVALID_INPUT
    assert DockerUnavailableError.exit_code == ExitCode.DOCKER_UNAVAILABLE
    assert ExecutionError.exit_code == ExitCode.EXECUTION_FAILED
