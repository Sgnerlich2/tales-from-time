"""tft validate, tft hash, and tft schema export, run through the CLI."""

import hashlib
import re

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


def test_validate_runs_only_schema_rules_on_a_single_file(episode):
    # A 9-second static shot breaks STATIC_SHOT_TOO_LONG, which is not a schema rule.
    episode.update("scenes.json", "SCN-003", duration_s=9.0)
    path = episode.path("scenes.json")
    result = invoke("validate", str(path))
    assert (result.exit_code, result.output) == (0, f"PASS {path} (1 files, 0 errors)\n")


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
