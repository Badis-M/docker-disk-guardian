"""Rich table reporter for terminal output."""

from io import StringIO

from rich.console import Console
from rich.table import Table

from docker_disk_guardian.models import CleanupPlan, Inventory, Resource


def format_bytes(value: int | None) -> str:
    if value is None:
        return "unknown"
    amount = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if amount < 1024 or unit == "TiB":
            return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{amount:.1f} TiB"


def render_inventory(inventory: Inventory, *, color: bool = True) -> str:
    table = Table(title="Docker Disk Inventory")
    table.add_column("Type")
    table.add_column("Name")
    table.add_column("ID")
    table.add_column("Size", justify="right")
    table.add_column("Created")

    groups: tuple[tuple[str, tuple[Resource, ...]], ...] = (
        ("container", inventory.containers),
        ("image", inventory.images),
        ("volume", inventory.volumes),
        ("network", inventory.networks),
        ("build_cache", inventory.build_cache),
    )
    for resource_type, resources in groups:
        for resource in sorted(resources, key=lambda item: (item.name, item.id)):
            table.add_row(
                resource_type,
                resource.name,
                resource.id[:12],
                format_bytes(resource.size_bytes),
                resource.created_at.isoformat(),
            )

    output = StringIO()
    console = Console(file=output, force_terminal=color, color_system="standard" if color else None)
    console.print(table)
    console.print(f"Known total: {format_bytes(inventory.total_known_bytes)}")
    return output.getvalue()


def render_plan(plan: CleanupPlan, *, color: bool = True) -> str:
    table = Table(title="Docker Cleanup Plan")
    table.add_column("Type")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Estimate", justify="right")
    table.add_column("Reasons")
    for decision in plan.decisions:
        style = "green" if decision.status == "candidate" else "yellow"
        table.add_row(
            decision.resource_type.value,
            decision.resource_name,
            f"[{style}]{decision.status.value}[/{style}]" if color else decision.status.value,
            format_bytes(decision.estimated_bytes),
            "; ".join(decision.reasons),
        )

    output = StringIO()
    console = Console(file=output, force_terminal=color, color_system="standard" if color else None)
    console.print(table)
    console.print(
        f"Candidates: {len(plan.candidates)} | "
        f"Estimated reclaimable: {format_bytes(plan.estimated_reclaimable_bytes)}"
    )
    return output.getvalue()
