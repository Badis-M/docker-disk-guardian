"""Deterministic policy evaluation for cleanup planning."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from docker_disk_guardian.config import CleanupPolicy
from docker_disk_guardian.models import (
    CleanupDecision,
    CleanupPlan,
    ContainerResource,
    ContainerState,
    DecisionStatus,
    ImageResource,
    Inventory,
    Resource,
)
from docker_disk_guardian.safety import protection_reasons


class CleanupPlanner:
    def __init__(
        self,
        policy: CleanupPolicy,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._policy = policy
        self._clock = clock or (lambda: datetime.now(UTC))

    def create_plan(self, inventory: Inventory) -> CleanupPlan:
        now = self._clock()
        decisions = [
            *(self._container_decision(item, now) for item in inventory.containers),
            *(self._image_decision(item, now) for item in inventory.images),
        ]
        decisions.sort(key=lambda item: (item.resource_type.value, item.resource_name, item.resource_id))
        return CleanupPlan(generated_at=now, decisions=tuple(decisions))

    def _container_decision(
        self, container: ContainerResource, now: datetime
    ) -> CleanupDecision:
        protected = protection_reasons(container, self._policy)
        if protected:
            return self._decision(container, DecisionStatus.PROTECTED, protected)
        if container.state != ContainerState.STOPPED:
            return self._decision(
                container,
                DecisionStatus.RETAINED,
                ("container is not in a safely removable stopped state",),
            )
        reference_time = container.finished_at or container.created_at
        return self._age_decision(
            container,
            now - reference_time,
            self._policy.retention.stopped_containers,
            "stopped container exceeds retention",
            "stopped container is within retention",
        )

    def _image_decision(self, image: ImageResource, now: datetime) -> CleanupDecision:
        protected = protection_reasons(image, self._policy)
        if protected:
            return self._decision(image, DecisionStatus.PROTECTED, protected)
        if not image.dangling:
            return self._decision(
                image,
                DecisionStatus.RETAINED,
                ("image is tagged and not eligible for dangling-image cleanup",),
            )
        return self._age_decision(
            image,
            now - image.created_at,
            self._policy.retention.dangling_images,
            "dangling image exceeds retention",
            "dangling image is within retention",
        )

    def _age_decision(
        self,
        resource: Resource,
        age: timedelta,
        retention: timedelta,
        candidate_reason: str,
        retained_reason: str,
    ) -> CleanupDecision:
        status = DecisionStatus.CANDIDATE if age >= retention else DecisionStatus.RETAINED
        reason = candidate_reason if status == DecisionStatus.CANDIDATE else retained_reason
        return self._decision(resource, status, (reason,))

    @staticmethod
    def _decision(
        resource: Resource,
        status: DecisionStatus,
        reasons: tuple[str, ...],
    ) -> CleanupDecision:
        return CleanupDecision(
            resource_type=resource.resource_type,
            resource_id=resource.id,
            resource_name=resource.name,
            status=status,
            reasons=reasons,
            estimated_bytes=resource.size_bytes,
        )

