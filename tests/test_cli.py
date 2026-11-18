"""tft validate, tft hash, and tft schema export, run through the CLI."""

import hashlib
import re

import pytest
from typer.testing import CliRunner

from tft.cli import app
from tft.contracts import json_schemas
from tft.textnorm import segment_hash

ERROR_LINE = re.compile(r"^ERROR \S+ \S+ [A-Z_]+ \S.*$")
runner = CliRunner()


def invoke(*args: str):
    return runner.invoke(app, list(args))


def test_validate_passes_a_valid_episode_folder(episode):
    result = invoke("validate", str(episode.root))
    assert (result.exit_code, result.output) == (0, f"PASS {episode.root} (7 files, 0 errors)\n")


def test_validate_prints_one_line_per_problem_and_fails(episode):
    episode.update("scenes.json", "SCN-003", duration_s=9.0)
    episode.update("release.json", chapters=[{"start": "0:00", "title": "Only chapter"}])
    result = invoke("validate", str(episode.root))
    lines = result.output.splitlines()
    assert result.exit_code == 1
    assert lines == [
        "ERROR scenes.json SCN-003 STATIC_SHOT_TOO_LONG static shot lasts 9 s; the limit is 8 s",
        "ERROR release.json - CHAPTERS_INVALID the chapter count is 1; at least 3 are required",
        f"FAIL {episode.root} (7 files, 2 errors)",
    ]
    assert all(ERROR_LINE.match(line) for line in lines[:-1])


def test_validate_counts_only_the_contract_files_present(episode):
    for name in ("scenes.json", "assets.json", "release.json"):
        episode.path(name).unlink()
    result = invoke("validate", str(episode.root))
    assert (result.exit_code, result.output) == (0, f"PASS {episode.root} (4 files, 0 errors)\n")


def test_validate_fails_a_12_second_static_shot_in_a_single_scenes_file(episode):
    episode.update("scenes.json", "SCN-003", duration_s=12.0)
    path = episode.path("scenes.json")
    result = invoke("validate", str(path))
    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "ERROR scenes.json SCN-003 STATIC_SHOT_TOO_LONG static shot lasts 12 s; the limit is 8 s",
        f"FAIL {path} (1 files, 1 errors)",
    ]


def _retries(data):
    data["stages"]["script"]["retries"] = 3


def _cost(data):
    data["cost_usd"]["model"] = 10.0


def _first(field, item_id, **fields):
    def change(data):
        next(entry for entry in data[field] if item_id in entry.values()).update(fields)

    return change


# Every rule that needs only its own file runs on a single file (D17).
SINGLE_FILE_RULES = [
    ("episode.json", _retries, "RETRY_LIMIT_EXCEEDED"),
    ("episode.json", _cost, "BUDGET_CAP_EXCEEDED"),
    ("claims.json", _first("claims", "CLM-004", conflict_group=None), "LONE_CONFLICT_GROUP"),
    ("script.json", _first("segments", "SEG-001", is_factual=True), "UNCITED_FACTUAL_SEGMENT"),
    ("script.json", _first("segments", "SEG-003", voice="narrator"), "QUOTE_VOICE_MISMATCH"),
    ("script.json", _first("segments", "SEG-004", text="Changed text."), "TEXT_HASH_MISMATCH"),
    ("script.json", _first("segments", "SEG-002", verified_hash=None), "STALE_VERIFICATION"),
    ("scenes.json", _first("scenes", "SCN-003", duration_s=9.0), "STATIC_SHOT_TOO_LONG"),
    ("release.json", lambda data: data.update(youtube_id="invented-id"), "UPLOAD_WITHOUT_APPROVAL"),
    ("release.json", lambda data: data.update(chapters=data["chapters"][:1]), "CHAPTERS_INVALID"),
]


def test_single_file_rules_cover_every_rule_that_needs_one_file():
    from tft.validate.runner import _RULES

    one_file = {rule.code for rule in _RULES if len(rule.needs) == 1 and not rule.folder_only}
    assert one_file == {code for _, _, code in SINGLE_FILE_RULES}


@pytest.mark.parametrize(("name", "change", "code"), SINGLE_FILE_RULES, ids=[c for _, _, c in SINGLE_FILE_RULES])
def test_validate_runs_each_single_file_rule_on_one_file(episode, name, change, code):
    episode.edit(name, change)
    result = invoke("validate", str(episode.path(name)))
    lines = result.output.splitlines()
    assert result.exit_code == 1
    assert [line.split(" ")[3] for line in lines[:-1]] == [code], lines


@pytest.mark.parametrize(
    "name",
    ["sources.json", "assets.json", "script.json"],
)
def test_validate_leaves_disk_and_cross_file_rules_to_folder_mode(episode, name):
    episode.path("sources/SRC-002.txt").unlink()  # SOURCE_FILE_MISSING in folder mode
    episode.path("assets/AST-001.png").unlink()  # ASSET_FILE_MISSING in folder mode
    episode.update("script.json", "SEG-004", claim_ids=["CLM-009"])
    episode.rehash("SEG-004")  # UNKNOWN_CLAIM in folder mode
    path = episode.path(name)
    assert invoke("validate", str(path)).output == f"PASS {path} (1 files, 0 errors)\n"
    assert {"SOURCE_FILE_MISSING", "ASSET_FILE_MISSING", "UNKNOWN_CLAIM"} <= set(episode.codes())


def test_validate_fails_an_empty_folder(tmp_path):
    result = invoke("validate", str(tmp_path))
    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "ERROR episode.json - EPISODE_FILE_MISSING the episode folder has no episode.json",
        f"FAIL {tmp_path} (0 files, 1 errors)",
    ]


def test_validate_reports_schema_problems_in_a_single_file(episode):
    episode.update("scenes.json", "SCN-003", duration_s=0)
    path = episode.path("scenes.json")
    result = invoke("validate", str(path))
    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "ERROR scenes.json SCN-003 SCHEMA_INVALID scenes[2].duration_s: Input should be greater than 0",
        f"FAIL {path} (1 files, 1 errors)",
    ]


def test_validate_reports_duplicate_ids_in_a_single_file(episode):
    data = episode.load("claims.json")
    data["claims"].append(dict(data["claims"][4]))
    episode.save("claims.json", data)
    path = episode.path("claims.json")
    result = invoke("validate", str(path))
    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "ERROR claims.json CLM-005 DUPLICATE_ID claim_id CLM-005 appears 2 times",
        f"FAIL {path} (1 files, 1 errors)",
    ]


def test_validate_reports_path_not_found(tmp_path):
    missing = tmp_path / "does-not-exist"
    result = invoke("validate", str(missing))
    assert (result.exit_code, result.output) == (2, f"ERROR - - PATH_NOT_FOUND {missing}\n")


def test_validate_rejects_a_file_that_is_not_a_contract(tmp_path):
    other = tmp_path / "topics.json"
    other.write_text("{}", encoding="utf-8")
    result = invoke("validate", str(other))
    assert result.exit_code == 2
    assert result.output.startswith(f"ERROR - - UNKNOWN_CONTRACT {other} (the file name must be one of:")


def test_hash_file_prints_the_sha256_of_the_raw_bytes(tmp_path):
    path = tmp_path / "sample.bin"
    path.write_bytes(b"line one\r\nline two\n")
    result = invoke("hash", "file", str(path))
    assert (result.exit_code, result.output) == (0, hashlib.sha256(b"line one\r\nline two\n").hexdigest() + "\n")


def test_hash_file_reports_a_missing_path_or_a_folder(tmp_path):
    missing = invoke("hash", "file", str(tmp_path / "nope.bin"))
    folder = invoke("hash", "file", str(tmp_path))
    assert (missing.exit_code, missing.output) == (2, f"ERROR - - PATH_NOT_FOUND {tmp_path / 'nope.bin'}\n")
    assert (folder.exit_code, folder.output) == (2, f"ERROR - - NOT_A_FILE {tmp_path}\n")


def test_hash_segment_ignores_claim_order():
    first = invoke("hash", "segment", "--text", "It sank.", "--claims", "CLM-002,CLM-001")
    second = invoke("hash", "segment", "--text", "It sank.", "--claims", "CLM-001,CLM-002")
    assert first.exit_code == second.exit_code == 0
    assert first.output == second.output == segment_hash("It sank.", ["CLM-001", "CLM-002"]) + "\n"
    assert re.fullmatch(r"[0-9a-f]{64}\n", first.output)


def test_hash_segment_without_claims():
    result = invoke("hash", "segment", "--text", "It sank.")
    assert (result.exit_code, result.output) == (0, segment_hash("It sank.", []) + "\n")


def test_schema_export_writes_all_seven_schemas(tmp_path):
    out = tmp_path / "schemas"
    result = invoke("schema", "export", "--out", str(out))
    expected = json_schemas()
    assert result.exit_code == 0
    assert sorted(path.name for path in out.iterdir()) == sorted(expected)
    for name, text in expected.items():
        assert (out / name).read_bytes() == text.encode("utf-8")
