"""Run the validator over an episode folder or a single contract file."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from tft.contracts import CONTRACT_FILES, CONTRACTS
from tft.validate import rules
from tft.validate.files import FileFact, probe, read_text
from tft.validate.loading import load_contract
from tft.validate.problems import RULE_CODES, Problem


@dataclass(frozen=True)
class Report:
    """The outcome of one validation run."""

    files: int  # contract files checked
    problems: list[Problem]

    @property
    def passed(self) -> bool:
        return not self.problems


@dataclass(frozen=True)
class _Inputs:
    models: dict[str, BaseModel]  # contracts present that passed their schema
    present: frozenset[str]  # contracts whose file exists, valid or not
    files: dict[str, FileFact]  # recorded relative path to what is there
    texts: dict[str, str | None]  # source text_path to its text


@dataclass(frozen=True)
class _Rule:
    code: str
    needs: tuple[str, ...]  # contracts that must be present and valid
    run: Callable[[_Inputs], list[Problem]]
    folder_only: bool = False  # True when the rule also reads files on disk or another file's presence


# Every rule after SCHEMA_INVALID and DUPLICATE_ID, in rule-table order. A rule that needs
# one contract and is not folder_only also runs when a single file is validated (D17).
_RULES: tuple[_Rule, ...] = (
    _Rule("RETRY_LIMIT_EXCEEDED", ("episode",), lambda i: rules.retry_limit_exceeded(i.models["episode"])),
    _Rule("BUDGET_CAP_EXCEEDED", ("episode",), lambda i: rules.budget_cap_exceeded(i.models["episode"])),
    _Rule(
        "SOURCE_FILE_MISSING",
        ("sources",),
        lambda i: rules.source_file_missing(i.models["sources"], i.files),
        folder_only=True,
    ),
    _Rule(
        "SOURCE_HASH_MISMATCH",
        ("sources",),
        lambda i: rules.source_hash_mismatch(i.models["sources"], i.files),
        folder_only=True,
    ),
    _Rule(
        "INSUFFICIENT_SOURCES",
        ("sources",),
        lambda i: rules.insufficient_sources(i.models["sources"], "script" in i.present),
        folder_only=True,
    ),
    _Rule(
        "UNKNOWN_SOURCE",
        ("claims", "sources"),
        lambda i: rules.unknown_source(i.models["claims"], i.models["sources"]),
    ),
    _Rule(
        "QUOTE_NOT_FOUND",
        ("claims", "sources"),
        lambda i: rules.quote_not_found(i.models["claims"], i.models["sources"], i.files, i.texts),
    ),
    _Rule("LONE_CONFLICT_GROUP", ("claims",), lambda i: rules.lone_conflict_group(i.models["claims"])),
    _Rule("UNKNOWN_CLAIM", ("script", "claims"), lambda i: rules.unknown_claim(i.models["script"], i.models["claims"])),
    _Rule(
        "REJECTED_CLAIM_CITED",
        ("script", "claims"),
        lambda i: rules.rejected_claim_cited(i.models["script"], i.models["claims"]),
    ),
    _Rule("UNCITED_FACTUAL_SEGMENT", ("script",), lambda i: rules.uncited_factual_segment(i.models["script"])),
    _Rule(
        "QUOTE_MISMATCH",
        ("script", "claims"),
        lambda i: rules.quote_mismatch(i.models["script"], i.models["claims"]),
    ),
    _Rule("QUOTE_VOICE_MISMATCH", ("script",), lambda i: rules.quote_voice_mismatch(i.models["script"])),
    _Rule("TEXT_HASH_MISMATCH", ("script",), lambda i: rules.text_hash_mismatch(i.models["script"])),
    _Rule("STALE_VERIFICATION", ("script",), lambda i: rules.stale_verification(i.models["script"])),
    _Rule(
        "UNKNOWN_SEGMENT",
        ("scenes", "script"),
        lambda i: rules.unknown_segment(i.models["scenes"], i.models["script"]),
    ),
    _Rule(
        "SEGMENT_HASH_MISMATCH",
        ("scenes", "script"),
        lambda i: rules.segment_hash_mismatch(i.models["scenes"], i.models["script"]),
    ),
    _Rule("STATIC_SHOT_TOO_LONG", ("scenes",), lambda i: rules.static_shot_too_long(i.models["scenes"])),
    _Rule("UNKNOWN_ASSET", ("scenes", "assets"), lambda i: rules.unknown_asset(i.models["scenes"], i.models["assets"])),
    _Rule(
        "ASSET_FILE_MISSING",
        ("assets",),
        lambda i: rules.asset_file_missing(i.models["assets"], i.files),
        folder_only=True,
    ),
    _Rule(
        "ASSET_HASH_MISMATCH",
        ("assets",),
        lambda i: rules.asset_hash_mismatch(i.models["assets"], i.files),
        folder_only=True,
    ),
    _Rule(
        "ASSET_RIGHTS_UNRESOLVED",
        ("assets", "scenes"),
        lambda i: rules.asset_rights_unresolved(i.models["assets"], i.models["scenes"]),
    ),
    _Rule("UPLOAD_WITHOUT_APPROVAL", ("release",), lambda i: rules.upload_without_approval(i.models["release"])),
    _Rule("CHAPTERS_INVALID", ("release",), lambda i: rules.chapters_invalid(i.models["release"])),
)

_FILE_ORDER = {f"{name}.json": index for index, name in enumerate(CONTRACTS)}
_CODE_ORDER = {code: index for index, code in enumerate(RULE_CODES)}


def _sorted(problems: list[Problem]) -> list[Problem]:
    """Group problems by file in contract order, then by code in rule-table order."""
    return sorted(problems, key=lambda p: (_FILE_ORDER.get(p.file, len(_FILE_ORDER)), _CODE_ORDER[p.code]))


def _schema_rules(path: Path, contract: str) -> tuple[BaseModel | None, list[Problem]]:
    """SCHEMA_INVALID and DUPLICATE_ID for one contract file."""
    model, problems = load_contract(path, contract)
    if model is not None:
        problems = problems + rules.duplicate_ids(contract, model)
    return model, problems


def validate_file(path: Path) -> Report:
    """Validate one contract file on its own (D17).

    Runs SCHEMA_INVALID, DUPLICATE_ID, and every rule that needs only this file. Rules that
    need another contract file, or files on disk, run only in folder mode. The contract type
    comes from the file name, which must be one of CONTRACT_FILES.
    """
    contract = CONTRACT_FILES[path.name]
    model, problems = _schema_rules(path, contract)
    if model is not None:
        inputs = _Inputs(models={contract: model}, present=frozenset({contract}), files={}, texts={})
        for rule in _RULES:
            if rule.needs == (contract,) and not rule.folder_only:
                problems += rule.run(inputs)
    return Report(files=1, problems=_sorted(problems))


def _gather_files(root: Path, models: dict[str, BaseModel]) -> tuple[dict[str, FileFact], dict[str, str | None]]:
    paths: list[str] = []
    sources = models.get("sources")
    if sources is not None:
        for source in sources.sources:
            paths += [source.local_path, source.text_path]
    assets = models.get("assets")
    if assets is not None:
        paths += [asset.path for asset in assets.assets]
    files = {path: probe(root, path) for path in dict.fromkeys(paths)}
    texts: dict[str, str | None] = {}
    if sources is not None and "claims" in models:
        for source in sources.sources:
            if files[source.text_path].ok and source.text_path not in texts:
                texts[source.text_path] = read_text(root, source.text_path)
    return files, texts


def validate_folder(root: Path) -> Report:
    """Validate an episode folder.

    First the folder structure (EPISODE_FILE_MISSING, UPSTREAM_FILE_MISSING), then the schema
    rules for every contract file present, then every other rule whose contract files are
    present and passed their schema. A file that is missing only fails the folder when
    episode.json is missing or a later file needs it (D20).
    """
    present = frozenset(contract for contract in CONTRACTS if (root / f"{contract}.json").is_file())
    problems = rules.episode_file_missing(present) + rules.upstream_file_missing(present)
    models: dict[str, BaseModel] = {}
    for contract in CONTRACTS:
        if contract not in present:
            continue
        model, file_problems = _schema_rules(root / f"{contract}.json", contract)
        problems += file_problems
        if model is not None:
            models[contract] = model
    files, texts = _gather_files(root, models)
    inputs = _Inputs(models=models, present=present, files=files, texts=texts)
    for rule in _RULES:
        if all(contract in models for contract in rule.needs):
            problems += rule.run(inputs)
    return Report(files=len(present), problems=_sorted(problems))
