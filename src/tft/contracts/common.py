"""Shared pieces of the contract models: the base model, ID types, and value types."""

from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, StringConstraints, WithJsonSchema


class ContractModel(BaseModel):
    """Base for every contract model: strict types, no extra fields, no NaN or infinity."""

    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


# IDs (IC7). d is an ASCII digit.
EpisodeId = Annotated[str, StringConstraints(pattern=r"^EP-[0-9]{4}$")]
SourceId = Annotated[str, StringConstraints(pattern=r"^SRC-[0-9]{3}$")]
ClaimId = Annotated[str, StringConstraints(pattern=r"^CLM-[0-9]{3}$")]
SegmentId = Annotated[str, StringConstraints(pattern=r"^SEG-[0-9]{3}$")]
SceneId = Annotated[str, StringConstraints(pattern=r"^SCN-[0-9]{3}$")]
AssetId = Annotated[str, StringConstraints(pattern=r"^AST-[0-9]{3}$")]
ConflictGroupId = Annotated[str, StringConstraints(pattern=r"^CG-[0-9]{3}$")]

# A SHA-256 digest as 64 lowercase hex characters, as tft hash prints it.
Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]

# A string with at least one non-whitespace character.
NonEmptyStr = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]

Stage = Literal[
    "topics",
    "sources",
    "claims",
    "script",
    "verify",
    "visuals",
    "assets",
    "narration",
    "render",
    "qa",
    "package",
]


def _reject_bool(value: Any) -> Any:
    # JSON true would otherwise pass as Literal[1], because True == 1 in Python.
    if isinstance(value, bool):
        raise ValueError("must be the integer 1, not a boolean")
    return value


def _require_bool(value: Any) -> Any:
    # JSON 1 would otherwise pass as Literal[True], because 1 == True in Python.
    if not isinstance(value, bool):
        raise ValueError("must be the boolean true")
    return value


SchemaVersion = Annotated[Literal[1], BeforeValidator(_reject_bool)]
TrueFlag = Annotated[Literal[True], BeforeValidator(_require_bool)]

# Paths inside JSON are relative to the episode folder and use forward slashes (IC10).
# The pattern is what the exported JSON Schema carries; _check_rel_path enforces the same
# rule in Python with clearer messages. tests/test_contracts.py checks that they agree.
_SEGMENT = r"(?:[^/\\:.][^/\\:]*|\.[^/\\:.][^/\\:]*|\.\.[^/\\:]+)"
REL_PATH_PATTERN = rf"^{_SEGMENT}(?:/{_SEGMENT})*$"


def _check_rel_path(value: str) -> str:
    if not value:
        raise ValueError("path must not be empty")
    if "\\" in value:
        raise ValueError("path must use forward slashes, not backslashes")
    if value.startswith("/") or ":" in value:
        raise ValueError("path must be relative to the episode folder, with no drive, scheme, or leading slash")
    if any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("path must not contain empty, '.' or '..' parts")
    return value


RelPath = Annotated[
    str,
    AfterValidator(_check_rel_path),
    WithJsonSchema({"type": "string", "pattern": REL_PATH_PATTERN}),
]
