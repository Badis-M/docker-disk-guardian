import os
from uuid import uuid4

import docker
import pytest
from docker.errors import DockerException, ImageNotFound

from docker_disk_guardian.docker_client import DockerSdkGateway

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("DDG_RUN_INTEGRATION") != "1",
        reason="set DDG_RUN_INTEGRATION=1 to run Docker integration tests",
    ),
]


def test_inventory_collects_only_created_labeled_fixture() -> None:
    """Create and remove only a uniquely labeled fixture owned by this test."""
    client = docker.from_env()
    fixture_id = uuid4().hex
    label = {"docker-disk-guardian.test-id": fixture_id}
    container = None
    try:
        try:
            client.images.get("busybox:1.36")
        except ImageNotFound:
            pytest.skip("busybox:1.36 is not available locally; integration tests never auto-pull")
        container = client.containers.create(
            "busybox:1.36",
            command=["sh", "-c", "exit 0"],
            name=f"ddg-test-{fixture_id[:12]}",
            labels=label,
        )
        container.start()
        container.wait(timeout=10)

        resources = DockerSdkGateway(client).list_containers()
        owned = [resource for resource in resources if resource.labels == label]

        assert len(owned) == 1
        assert owned[0].id == container.id
    except DockerException as exc:
        pytest.fail(f"Docker integration fixture failed: {exc}")
    finally:
        if container is not None:
            container.remove(force=True)
        client.close()
