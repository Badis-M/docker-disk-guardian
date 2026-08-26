"""Application-specific exceptions with stable exit codes."""

from enum import IntEnum


class ExitCode(IntEnum):
    """Process exit codes exposed by the CLI."""

    SUCCESS = 0
    INVALID_INPUT = 2
    DOCKER_UNAVAILABLE = 3
    EXECUTION_FAILED = 4
    INTERRUPTED = 130


class GuardianError(Exception):
    """Base class for expected application failures."""

    exit_code = ExitCode.INVALID_INPUT


class ConfigurationError(GuardianError):
    """Raised when a supplied policy or option is invalid."""


class DockerUnavailableError(GuardianError):
    """Raised when the Docker daemon cannot be reached."""

    exit_code = ExitCode.DOCKER_UNAVAILABLE


class ExecutionError(GuardianError):
    """Raised when cleanup cannot be completed safely."""

    exit_code = ExitCode.EXECUTION_FAILED
