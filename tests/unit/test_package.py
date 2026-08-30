from docker_disk_guardian import __version__


def test_package_version() -> None:
    assert __version__ == "1.0.0"
