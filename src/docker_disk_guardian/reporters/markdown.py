"""Portable Markdown reports for inventory and cleanup review."""

from docker_disk_guardian.models import CleanupPlan, Inventory, Resource
from docker_disk_guardian.reporters.table import format_bytes


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_inventory(inventory: Inventory) -> str:
    lines = [
        "# Docker Disk Inventory",
        "",
        f"Collected at: `{inventory.collected_at.isoformat()}`",
        "",
        "| Type | Name | ID | Size |",
        "|---|---|---|---:|",
    ]
    groups: tuple[tuple[str, tuple[Resource, ...]], ...] = (
        ("container", inventory.containers),
        ("image", inventory.images),
        ("volume", inventory.volumes),
        ("network", inventory.networks),
        ("build_cache", inventory.build_cache),
    )
    for resource_type, resources in groups:
        for resource in sorted(resources, key=lambda item: (item.name, item.id)):
            lines.append(
                f"| {resource_type} | {_escape(resource.name)} | `{resource.id[:12]}` | "
                f"{format_bytes(resource.size_bytes)} |"
            )
    lines.extend(["", f"Known total: **{format_bytes(inventory.total_known_bytes)}**", ""])
    return "\n".join(lines)


def render_plan(plan: CleanupPlan) -> str:
    lines = [
        "# Docker Cleanup Plan",
        "",
        f"Generated at: `{plan.generated_at.isoformat()}`",
        "",
        "| Type | Name | Status | Estimate | Reasons |",
        "|---|---|---|---:|---|",
    ]
    for decision in plan.decisions:
        lines.append(
            f"| {decision.resource_type.value} | {_escape(decision.resource_name)} | "
            f"{decision.status.value} | {format_bytes(decision.estimated_bytes)} | "
            f"{_escape('; '.join(decision.reasons))} |"
        )
    lines.extend(
        [
            "",
            f"Candidates: **{len(plan.candidates)}**",
            f"Estimated reclaimable: **{format_bytes(plan.estimated_reclaimable_bytes)}**",
            "",
        ]
    )
    return "\n".join(lines)

