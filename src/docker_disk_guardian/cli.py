"""Command-line interface for Docker Disk Guardian."""

from typing import Annotated

import typer

from docker_disk_guardian import __version__

app = typer.Typer(
    name="docker-disk-guardian",
    help="Inspect, plan, and safely clean local Docker disk usage.",
    no_args_is_help=True,
)


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


if __name__ == "__main__":
    app()

