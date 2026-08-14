"""Command-line interface for Docker Disk Guardian."""

from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from docker_disk_guardian import __version__
from docker_disk_guardian.config import CleanupPolicy, load_policy
from docker_disk_guardian.docker_client import DockerSdkGateway
from docker_disk_guardian.errors import GuardianError
from docker_disk_guardian.inventory import ALL_RESOURCE_TYPES, InventoryService
from docker_disk_guardian.models import ResourceType
from docker_disk_guardian.reporters.json import render_inventory as render_json_inventory
from docker_disk_guardian.reporters.json import render_plan as render_json_plan
from docker_disk_guardian.reporters.markdown import render_inventory as render_markdown_inventory
from docker_disk_guardian.reporters.markdown import render_plan as render_markdown_plan
from docker_disk_guardian.reporters.table import render_inventory as render_table_inventory
from docker_disk_guardian.reporters.table import render_plan as render_table_plan
from docker_disk_guardian.planner import CleanupPlanner

app = typer.Typer(
    name="docker-disk-guardian",
    help="Inspect, plan, and safely clean local Docker disk usage.",
    no_args_is_help=True,
)
policy_app = typer.Typer(help="Validate and inspect cleanup policies.")
app.add_typer(policy_app, name="policy")


class OutputFormat(StrEnum):
    TABLE = "table"
    JSON = "json"
    MARKDOWN = "markdown"


def _emit(content: str, output: Path | None) -> None:
    if output is None:
        typer.echo(content, nl=False)
        return
    try:
        output.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(f"Cannot write output file: {exc}", param_hint="--output") from exc


@app.command()
def version(
    short: Annotated[
        bool,
        typer.Option("--short", help="Print only the semantic version."),
    ] = False,
) -> None:
    """Show the installed Docker Disk Guardian version."""
    value = __version__ if short else f"docker-disk-guardian {__version__}"
    typer.echo(value)


@app.command("inspect")
def inspect_command(
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", help="Report format."),
    ] = OutputFormat.TABLE,
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Write the report to this path."),
    ] = None,
    include: Annotated[
        list[ResourceType] | None,
        typer.Option("--include", help="Include only this resource type. Repeatable."),
    ] = None,
    exclude: Annotated[
        list[ResourceType] | None,
        typer.Option("--exclude", help="Exclude this resource type. Repeatable."),
    ] = None,
) -> None:
    """Inspect Docker disk usage without changing any resources."""
    selected = set(include) if include else set(ALL_RESOURCE_TYPES)
    selected.difference_update(exclude or ())
    if not selected:
        raise typer.BadParameter("At least one resource type must be selected.")

    gateway: DockerSdkGateway | None = None
    try:
        gateway = DockerSdkGateway.connect()
        inventory = InventoryService(gateway).collect(selected)
        if output_format == OutputFormat.JSON:
            report = render_json_inventory(inventory)
        elif output_format == OutputFormat.MARKDOWN:
            report = render_markdown_inventory(inventory)
        else:
            report = render_table_inventory(inventory, color=output is None)
        _emit(report, output)
    except GuardianError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=int(exc.exit_code)) from exc
    finally:
        if gateway is not None:
            gateway.close()


@policy_app.command("validate")
def validate_policy(path: Annotated[Path, typer.Argument(help="YAML policy path.")]) -> None:
    """Validate a cleanup policy without connecting to Docker."""
    try:
        policy = load_policy(path)
    except GuardianError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=int(exc.exit_code)) from exc
    typer.echo(f"Policy is valid (version {policy.version}).")


@app.command("plan")
def plan_command(
    policy_path: Annotated[
        Path | None,
        typer.Option("--policy", help="YAML cleanup policy. Defaults to safe built-ins."),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", help="Report format."),
    ] = OutputFormat.TABLE,
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Write the report to this path."),
    ] = None,
) -> None:
    """Evaluate cleanup candidates without changing Docker."""
    gateway: DockerSdkGateway | None = None
    try:
        policy = load_policy(policy_path) if policy_path is not None else CleanupPolicy()
        gateway = DockerSdkGateway.connect()
        inventory = InventoryService(gateway).collect()
        plan = CleanupPlanner(policy).create_plan(inventory)
        if output_format == OutputFormat.JSON:
            report = render_json_plan(plan)
        elif output_format == OutputFormat.MARKDOWN:
            report = render_markdown_plan(plan)
        else:
            report = render_table_plan(plan, color=output is None)
        _emit(report, output)
    except GuardianError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=int(exc.exit_code)) from exc
    finally:
        if gateway is not None:
            gateway.close()


if __name__ == "__main__":
    app()
