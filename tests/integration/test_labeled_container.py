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
    image = os.getenv("DDG_TEST_IMAGE", "busybox:1.36")
    container = None
    try:
        try:
            client.images.get(image)
        except ImageNotFound:
            pytest.fail(
                "The explicitly prepared fixture image is absent; no automatic pull is allowed"
            )
        container = client.containers.create(
            image,
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
