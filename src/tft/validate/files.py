"""Facts about the files that sources.json and assets.json record.

This module does the reading so the rules can stay pure. It only reads files inside the
episode folder: a recorded path that resolves outside it is reported, never opened.
"""

from dataclasses import dataclass
from pathlib import Path

from tft.textnorm import file_sha256


@dataclass(frozen=True)
class FileFact:
    """What the validator found at one recorded path."""

    ok: bool  # a readable regular file inside the episode folder
    detail: str = ""  # why not, when ok is False
    sha256: str | None = None


def _inside(root: Path, rel_path: str) -> Path | None:
    target = (root / rel_path).resolve()
    return target if target.is_relative_to(root.resolve()) else None


def probe(root: Path, rel_path: str) -> FileFact:
    """Check that rel_path is a file inside the episode folder, and hash it."""
    target = _inside(root, rel_path)
    if target is None:
        return FileFact(False, "is outside the episode folder")
    if not target.is_file():
        return FileFact(False, "does not exist")
    try:
        return FileFact(True, sha256=file_sha256(target))
    except OSError as exc:
        return FileFact(False, f"cannot be read ({exc.strerror})")


def read_text(root: Path, rel_path: str) -> str | None:
    """The file's text, or None if it is outside the folder, unreadable, or not valid UTF-8."""
    target = _inside(root, rel_path)
    if target is None:
        return None
    try:
        return target.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
