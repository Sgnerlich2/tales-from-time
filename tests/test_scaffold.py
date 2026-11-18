"""M0.1 scaffold checks: package version, CLI, .env.example, and git ignore rules."""

import subprocess
import tomllib
from pathlib import Path

from typer.testing import CliRunner

import tft
from tft.cli import app

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_NAMES = ["ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY", "TFT_WORKSPACE", "BACKUP_REMOTE"]


def git(*args: str) -> subprocess.CompletedProcess[str]:
    """Run git in the repo root and capture its output."""
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )


def env_example_entries() -> tuple[list[tuple[str, bool, bool]], list[int]]:
    """Parse .env.example into (name, has_value, has_comment_above) entries, plus the
    numbers of lines that are not NAME= assignments. Values are never returned, so a
    failing test cannot print one."""
    lines = (REPO_ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    entries: list[tuple[str, bool, bool]] = []
    bad_lines: list[int] = []
    for number, line in enumerate(lines, start=1):
        if not line.strip() or line.startswith("#"):
            continue
        name, equals, value = line.partition("=")
        if not equals:
            bad_lines.append(number)
            continue
        has_comment_above = number > 1 and lines[number - 2].startswith("#")
        entries.append((name, value != "", has_comment_above))
    return entries, bad_lines


def test_package_version() -> None:
    assert tft.__version__ == "0.1.0"


def test_package_version_matches_pyproject() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == tft.__version__


def test_cli_prints_version() -> None:
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output == "tft 0.1.0\n"


def test_env_example_lists_the_four_names_with_empty_values() -> None:
    entries, bad_lines = env_example_entries()
    assert bad_lines == []
    assert sorted(name for name, _, _ in entries) == sorted(ENV_NAMES)
    assert [name for name, has_value, _ in entries if has_value] == []
    assert [name for name, _, has_comment_above in entries if not has_comment_above] == []


def test_git_ignores_env_and_workspace_files() -> None:
    result = git("check-ignore", ".env", "workspace/x.json")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [".env", "workspace/x.json"]


def test_git_keeps_env_example_and_workspace_gitkeep() -> None:
    # Exit code 1 means no path is ignored; --no-index applies the rules to tracked files too.
    result = git("check-ignore", "--no-index", ".env.example", "workspace/.gitkeep")
    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout == ""


def test_no_env_file_is_tracked() -> None:
    result = git("ls-files", "-z")
    assert result.returncode == 0, result.stderr
    tracked_env_files = [
        path
        for path in result.stdout.split("\0")
        if (name := path.rsplit("/", 1)[-1]) == ".env"
        or (name.startswith(".env.") and name != ".env.example")
    ]
    assert tracked_env_files == []
