"""Quote normalization and hashing (IC8, IC9), using the standard library only.

normalize_quote changes only punctuation and whitespace. It applies no NFKC or other
Unicode normalization, so the charter's word-for-word rule holds: 10² never matches 102.
"""

import hashlib
import re
from collections.abc import Iterable
from pathlib import Path

_CHARACTER_MAP = str.maketrans(
    {
        # Curly single quotes, including low-9 and reversed-9 forms, to a straight quote.
        "‘": "'",
        "’": "'",
        "‚": "'",
        "‛": "'",
        # Curly double quotes, including low-9 and reversed-9 forms, to a straight quote.
        "“": '"',
        "”": '"',
        "„": '"',
        "‟": '"',
        # En dash, em dash, and minus sign to a hyphen.
        "–": "-",
        "—": "-",
        "−": "-",
        # The ellipsis character to three dots.
        "…": "...",
        # Soft hyphens are removed.
        "­": None,
    }
)

# A hyphen at a line break (LF, CRLF, or CR) between two letters. Spaces or tabs on either
# side of the line break count as part of it. Letters are Unicode letters.
_LETTER = r"[^\W\d_]"
_LINE_BREAK_HYPHEN = re.compile(rf"(?<={_LETTER})-[^\S\r\n]*(?:\r\n|\r|\n)[^\S\r\n]*(?={_LETTER})")
_WHITESPACE_RUN = re.compile(r"\s+")


def normalize_quote(text: str, keep_linebreak_hyphen: bool = False) -> str:
    """Normalize quote or source text for comparison.

    Curly quotes become straight, en dash, em dash, and minus sign become a hyphen, the
    ellipsis character becomes three dots, and soft hyphens are removed. A hyphen at a line
    break between two letters is joined ("well-\\nknown" becomes "wellknown"), or with
    keep_linebreak_hyphen=True only the line break goes ("well-known"). Every whitespace run
    becomes one space and the ends are stripped. Case and wording stay unchanged.
    """
    text = text.translate(_CHARACTER_MAP)
    text = _LINE_BREAK_HYPHEN.sub("-" if keep_linebreak_hyphen else "", text)
    return _WHITESPACE_RUN.sub(" ", text).strip()


def segment_hash(text: str, claim_ids: Iterable[str]) -> str:
    """SHA-256 hex of normalize_quote(text), a newline, then the sorted claim IDs joined by commas.

    The string is encoded as UTF-8 before hashing.
    """
    payload = normalize_quote(text) + "\n" + ",".join(sorted(claim_ids))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path: str | Path) -> str:
    """SHA-256 hex of the file's raw bytes."""
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


class NormalizedText:
    """A source text normalized both ways, for repeated quote lookups."""

    def __init__(self, text: str) -> None:
        self.joined = normalize_quote(text)
        self.kept = normalize_quote(text, keep_linebreak_hyphen=True)

    def contains(self, quote: str) -> bool:
        """True if the normalized quote is in the normalized text with line-break hyphens
        joined, or with them kept. An empty normalized quote never matches."""
        for keep, haystack in ((False, self.joined), (True, self.kept)):
            needle = normalize_quote(quote, keep_linebreak_hyphen=keep)
            if needle and needle in haystack:
                return True
        return False


def quote_in_text(quote: str, text: str) -> bool:
    """True if the quote appears in the text under the QUOTE_NOT_FOUND matching rule."""
    return NormalizedText(text).contains(quote)
