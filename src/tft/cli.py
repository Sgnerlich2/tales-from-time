"""Command-line interface for the Tales From Time pipeline."""

from pathlib import Path
from typing import Annotated

import typer

from tft import __version__
from tft.contracts import CONTRACT_FILES, json_schemas
from tft.textnorm import file_sha256, segment_hash
from tft.validate import validate_file, validate_folder

app = typer.Typer(add_completion=False, no_args_is_help=True)
hash_app = typer.Typer(no_args_is_help=True, help="Print SHA-256 hashes. Read-only.")
schema_app = typer.Typer(no_args_is_help=True, help="Export the contract JSON Schemas.")
app.add_typer(hash_app, name="hash")
app.add_typer(schema_app, name="schema")

# Exit codes for tft validate.
EXIT_PASS, EXIT_FAIL, EXIT_USAGE = 0, 1, 2


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


@app.command()
def validate(path: Annotated[str, typer.Argument(help="An episode folder or one contract file.")]) -> None:
    """Check an episode folder, or one contract file, against the contracts and rules.

    A folder gets every rule whose files are present. A single file gets the schema rules
    only (SCHEMA_INVALID and DUPLICATE_ID). Exit code 0 means PASS, 1 FAIL, 2 bad path.
    """
    target = Path(path)
    if not target.exists():
        typer.echo(f"ERROR - - PATH_NOT_FOUND {path}")
        raise typer.Exit(EXIT_USAGE)
    if target.is_dir():
        report = validate_folder(target)
    elif target.name in CONTRACT_FILES:
        report = validate_file(target)
    else:
        typer.echo(f"ERROR - - UNKNOWN_CONTRACT {path} (the file name must be one of: {', '.join(CONTRACT_FILES)})")
        raise typer.Exit(EXIT_USAGE)
    for problem in report.problems:
        typer.echo(problem.line())
    verdict = "PASS" if report.passed else "FAIL"
    typer.echo(f"{verdict} {path} ({report.files} files, {len(report.problems)} errors)")
    raise typer.Exit(EXIT_PASS if report.passed else EXIT_FAIL)


@hash_app.command("file")
def hash_file(path: Annotated[str, typer.Argument(help="The file to hash.")]) -> None:
    """Print the SHA-256 of a file's raw bytes."""
    target = Path(path)
    if not target.exists():
        typer.echo(f"ERROR - - PATH_NOT_FOUND {path}")
        raise typer.Exit(EXIT_USAGE)
    if not target.is_file():
        typer.echo(f"ERROR - - NOT_A_FILE {path}")
        raise typer.Exit(EXIT_USAGE)
    typer.echo(file_sha256(target))


@hash_app.command("segment")
def hash_segment(
    text: Annotated[str, typer.Option("--text", help="The segment text.")],
    claims: Annotated[str, typer.Option("--claims", help="Claim IDs separated by commas, e.g. CLM-001,CLM-002.")] = "",
) -> None:
    """Print a segment hash: SHA-256 of the normalized text, a newline, and the sorted claim IDs."""
    claim_ids = [claim_id.strip() for claim_id in claims.split(",") if claim_id.strip()]
    typer.echo(segment_hash(text, claim_ids))


@schema_app.command("export")
def schema_export(
    out: Annotated[Path, typer.Option("--out", help="Folder to write the schema files into.")] = Path("schemas"),
) -> None:
    """Write <contract>.schema.json for all seven contracts (default folder: schemas)."""
    out.mkdir(parents=True, exist_ok=True)
    for file_name, text in json_schemas().items():
        target = out / file_name
        target.write_text(text, encoding="utf-8", newline="\n")
        typer.echo(f"wrote {target.as_posix()}")
