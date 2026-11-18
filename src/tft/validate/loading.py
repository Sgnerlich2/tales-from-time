"""Read one contract file and check it against its model (SCHEMA_INVALID)."""

import codecs
import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from tft.contracts import CONTRACTS
from tft.validate.problems import Problem

# Contract name to (list field, ID field), for files whose entries carry IDs.
ID_FIELDS: dict[str, tuple[str, str]] = {
    "sources": ("sources", "source_id"),
    "claims": ("claims", "claim_id"),
    "script": ("segments", "segment_id"),
    "scenes": ("scenes", "scene_id"),
    "assets": ("assets", "asset_id"),
}

_ID_TOKEN = re.compile(r"^(?:EP-[0-9]{4}|(?:SRC|CLM|SEG|SCN|AST|CG)-[0-9]{3})$")


class _RejectedJson(ValueError):
    """JSON that parses in Python but is not accepted in a contract file."""


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _RejectedJson(f"duplicate key {key!r} in a JSON object")
        result[key] = value
    return result


def _reject_constant(name: str) -> Any:
    raise _RejectedJson(f"{name} is not valid JSON")


def _format_location(location: tuple[int | str, ...]) -> str:
    # ("scenes", 2, "duration_s") becomes scenes[2].duration_s; dict-key errors end in [key].
    text = ""
    for part in location:
        if isinstance(part, int):
            text += f"[{part}]"
        elif part == "[key]":
            text += "[key]"
        else:
            text += f".{part}" if text else part
    return text or "(file)"


def _item_id(contract: str, raw: Any, location: tuple[int | str, ...]) -> str:
    """The ID of the list entry an error points into, if the raw JSON has a well-formed one."""
    fields = ID_FIELDS.get(contract)
    if fields is None or len(location) < 2 or location[0] != fields[0] or not isinstance(location[1], int):
        return "-"
    entries = raw.get(fields[0]) if isinstance(raw, dict) else None
    if not isinstance(entries, list) or not 0 <= location[1] < len(entries):
        return "-"
    entry = entries[location[1]]
    candidate = entry.get(fields[1]) if isinstance(entry, dict) else None
    return candidate if isinstance(candidate, str) and _ID_TOKEN.match(candidate) else "-"


def load_contract(path: Path, contract: str) -> tuple[BaseModel | None, list[Problem]]:
    """Validate one contract file against its model.

    Returns the parsed model and no problems, or None and one SCHEMA_INVALID problem per
    error. Contract files must be UTF-8 without a byte order mark, strict JSON (no NaN or
    Infinity), with no repeated keys in an object.
    """
    file_name = f"{contract}.json"

    def invalid(message: str, item_id: str = "-") -> Problem:
        return Problem(file_name, item_id, "SCHEMA_INVALID", " ".join(message.split()))

    try:
        data = path.read_bytes()
    except OSError as exc:
        return None, [invalid(f"cannot read the file ({exc.strerror})")]
    if data.startswith(codecs.BOM_UTF8):
        return None, [invalid("the file starts with a UTF-8 byte order mark; save it as UTF-8 without one")]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return None, [invalid(f"the file is not valid UTF-8 (byte {exc.start})")]
    try:
        raw = json.loads(text, object_pairs_hook=_object_without_duplicate_keys, parse_constant=_reject_constant)
    except _RejectedJson as exc:
        return None, [invalid(str(exc))]
    except json.JSONDecodeError as exc:
        return None, [invalid(f"not valid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}")]
    try:
        model = CONTRACTS[contract].model_validate_json(text)
    except ValidationError as exc:
        return None, [
            invalid(f"{_format_location(error['loc'])}: {error['msg']}", _item_id(contract, raw, error["loc"]))
            for error in exc.errors(include_url=False, include_input=False)
        ]
    return model, []
