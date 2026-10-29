from importlib.metadata import version

from docker_disk_guardian import __version__


def test_package_version() -> None:
    assert __version__ == version("docker-disk-guardian")
