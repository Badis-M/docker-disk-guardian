"""Deterministic JSON inventory output."""

import json
from typing import Any

from docker_disk_guardian.models import CleanupPlan, Inventory


def inventory_document(inventory: Inventory) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "inventory",
        "collected_at": inventory.collected_at.isoformat(),
        "known_total_bytes": inventory.total_known_bytes,
        "resources": {
            "containers": [item.model_dump(mode="json") for item in inventory.containers],
            "images": [item.model_dump(mode="json") for item in inventory.images],
            "volumes": [item.model_dump(mode="json") for item in inventory.volumes],
            "networks": [item.model_dump(mode="json") for item in inventory.networks],
            "build_cache": [item.model_dump(mode="json") for item in inventory.build_cache],
        },
    }


def render_inventory(inventory: Inventory) -> str:
    return json.dumps(inventory_document(inventory), indent=2, sort_keys=True) + "\n"


def plan_document(plan: CleanupPlan) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "cleanup_plan",
        "generated_at": plan.generated_at.isoformat(),
        "candidate_count": len(plan.candidates),
        "estimated_reclaimable_bytes": plan.estimated_reclaimable_bytes,
        "decisions": [decision.model_dump(mode="json") for decision in plan.decisions],
    }


def render_plan(plan: CleanupPlan) -> str:
    return json.dumps(plan_document(plan), indent=2, sort_keys=True) + "\n"
