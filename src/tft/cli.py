"""Command-line interface for the Tales From Time pipeline."""

from typing import Annotated

import typer

from tft import __version__

app = typer.Typer(add_completion=False, no_args_is_help=True)


def _print_version(value: bool) -> None:
    """Print the version and exit before any command runs."""
    if value:
        typer.echo(f"tft {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Print the version and exit.",
            callback=_print_version,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Tales From Time: turn an approved topic into a source-backed history video."""
