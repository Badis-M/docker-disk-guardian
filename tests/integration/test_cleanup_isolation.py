"""Deletion tests operate only on UUID-owned fixtures in a disposable Docker engine."""

import os
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import docker
import pytest
from docker.errors import NotFound

from docker_disk_guardian.config import CleanupPolicy
from docker_disk_guardian.docker_client import DockerSdkGateway
from docker_disk_guardian.executor import CleanupExecutor
from docker_disk_guardian.models import DecisionStatus, Inventory
from docker_disk_guardian.planner import CleanupPlanner

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("DDG_RUN_INTEGRATION") != "1", reason="explicit Docker test opt-in required"
    ),
]


def test_volume_protection_and_targeted_apply_are_isolated() -> None:
    client = docker.from_env()
    token = uuid4().hex
    labels = {"docker-disk-guardian.test-id": token}
    volumes = []
    containers = []
    image = os.getenv("DDG_TEST_IMAGE", "busybox:1.36")
    gateway = DockerSdkGateway(client)
    now = datetime.now(UTC) + timedelta(days=1)
    try:
        client.images.get(image)
        volumes.append(client.volumes.create(name=token * 2, labels=labels))
        volumes.append(client.volumes.create(name="ddg-data-" + token, labels=labels))
        volumes.append(client.volumes.create(name="ddg-used-" + token, labels=labels))
        running = client.containers.create(
            image,
            command=["sleep", "300"],
            labels=labels,
            name="ddg-running-" + token,
            volumes={volumes[2].name: {"bind": "/data"}},
        )
        containers.append(running)
        running.start()
        expected_ids = {item.id for item in containers}
        expected_names = {item.name for item in volumes}
        inventory = Inventory(
            collected_at=now,
            containers=tuple(item for item in gateway.list_containers() if item.id in expected_ids),
            volumes=tuple(item for item in gateway.list_volumes() if item.name in expected_names),
        )
        assert len(inventory.containers) == 1
        assert len(inventory.volumes) == 3
        safe = CleanupPlanner(CleanupPolicy(), clock=lambda: now).create_plan(inventory)
        assert all(item.status == DecisionStatus.PROTECTED for item in safe.decisions)
        policy = CleanupPolicy.model_validate({"volumes": {"allow_named_volume_deletion": True}})
        plan = CleanupPlanner(policy, clock=lambda: now).create_plan(inventory)
        assert {item.resource_id for item in plan.candidates} == expected_names - {volumes[2].name}
        result = CleanupExecutor(gateway, policy, clock=lambda: now).execute(plan, inventory)
        assert result.succeeded == 2
        assert result.failed == 0
        running.reload()
        assert running.status == "running"
        client.volumes.get(volumes[2].name)
        for volume in volumes[:2]:
            with pytest.raises(NotFound):
                client.volumes.get(volume.name)
    finally:
        # Never enumerate-and-prune: cleanup is restricted to objects created above.
        try:
            for container in containers:
                container.remove(force=True)
            for volume in volumes:
                with suppress(NotFound):
                    volume.remove()
        finally:
            client.close()
