"""Pass and fail cases for every rule code, each built in tmp_path from the invented episode.

Test names contain the rule code in lowercase, so `pytest -k quote_not_found` finds them.
A pass case asserts the whole folder validates clean; a fail case asserts the rule's code
and no other.
"""

import socket

import pytest

from tft.validate import validate_file, validate_folder
from tft.validate.files import probe

ZERO_HASH = "0" * 64
CONTRACT_FILES = [
    "episode.json",
    "sources.json",
    "claims.json",
    "script.json",
    "scenes.json",
    "assets.json",
    "release.json",
]


def test_baseline_episode_passes_every_rule(episode):
    episode.passes()


# SCHEMA_INVALID


@pytest.mark.parametrize("name", CONTRACT_FILES)
def test_schema_invalid_passes_for_a_valid_file(episode, name):
    assert validate_file(episode.path(name)).problems == []


@pytest.mark.parametrize("name", CONTRACT_FILES)
def test_schema_invalid_fails_without_episode_id(episode, name):
    episode.edit(name, lambda data: data.pop("episode_id"))
    problem = episode.only("SCHEMA_INVALID")[0]
    assert (problem.file, problem.message) == (name, "episode_id: Field required")


@pytest.mark.parametrize(
    ("name", "item_id", "fields", "expected"),
    [
        ("scenes.json", "SCN-002", {"duration_s": 0}, "scenes[1].duration_s: Input should be greater than 0"),
        (
            "scenes.json",
            "SCN-003",
            {"citation": None},
            "scenes[2].citation: Value error, citation is required when component is document_quote",
        ),
        ("scenes.json", "SCN-001", {"motion": "zoom"}, "scenes[0].motion: Input should be 'static' or 'animated'"),
        ("claims.json", "CLM-002", {"quote": "  "}, "claims[1].quote: String should match pattern"),
        ("claims.json", "CLM-003", {"conflict_group": "CG-1"}, "claims[2].conflict_group: String should match pattern"),
        ("claims.json", "CLM-001", {"claim_id": "CLM-0001"}, "claims[0].claim_id: String should match pattern"),
        (
            "sources.json",
            "SRC-001",
            {"local_path": "sources\\SRC-001.pdf"},
            "sources[0].local_path: Value error, path must use forward slashes",
        ),
        ("sources.json", "SRC-002", {"text_path": "../SRC-002.txt"}, "sources[1].text_path: Value error, path must not"),
        ("sources.json", "SRC-002", {"date": "1901-02-29"}, "sources[1].date: Value error, day is out of range"),
        ("sources.json", "SRC-003", {"sha256": "A" * 64}, "sources[2].sha256: String should match pattern"),
        ("sources.json", "SRC-004", {"bias_note": ""}, "sources[3].bias_note: String should have at least 1 character"),
        ("script.json", "SEG-001", {"act": True}, "segments[0].act: Input should be a valid integer"),
        ("script.json", "SEG-001", {"act": 6}, "segments[0].act: Input should be less than or equal to 5"),
        ("script.json", "SEG-002", {"is_factual": "true"}, "segments[1].is_factual: Input should be a valid boolean"),
        ("assets.json", "AST-001", {"licence": "none"}, "assets[0].licence: Extra inputs are not permitted"),
    ],
)
def test_schema_invalid_fails_and_names_the_field(episode, name, item_id, fields, expected):
    episode.update(name, item_id, **fields)
    problems = episode.only("SCHEMA_INVALID")
    assert len(problems) == 1 and problems[0].message.startswith(expected), [p.line() for p in problems]
    assert problems[0].item_id == (item_id if "claim_id" not in fields else "-")


@pytest.mark.parametrize(
    ("name", "fields", "expected"),
    [
        ("episode.json", {"schema_version": 2}, "schema_version: Input should be 1"),
        ("episode.json", {"schema_version": True}, "schema_version: Value error, must be the integer 1"),
        ("episode.json", {"stages": {"scripting": {"status": "done", "retries": 0}}}, "stages.scripting[key]:"),
        ("episode.json", {"stages": {"script": {"status": "done", "retries": -1}}}, "stages.script.retries: Input"),
        (
            "episode.json",
            {"cost_usd": {"model": -1.0, "voice": 0.0, "assets": 0.0, "other": 0.0}},
            "cost_usd.model: Input should be greater than or equal to 0",
        ),
        ("episode.json", {"status": "paused"}, "status: Input should be"),
        ("episode.json", {"notes": "extra"}, "notes: Extra inputs are not permitted"),
        ("script.json", {"title_options": []}, "title_options: List should have at least 1 item"),
        ("script.json", {"title_options": ["x"] * 6}, "title_options: List should have at most 5 items"),
        ("script.json", {"title_options": ["x" * 101]}, "title_options[0]: String should have at most 100"),
        ("script.json", {"target_words": 0}, "target_words: Input should be greater than 0"),
        ("release.json", {"visibility": "public"}, "visibility: Input should be 'private'"),
        ("release.json", {"synthetic_disclosure": False}, "synthetic_disclosure: Input should be True"),
        ("release.json", {"synthetic_disclosure": 1}, "synthetic_disclosure: Value error, must be the boolean true"),
        ("release.json", {"chapters": [{"start": "0:00:0", "title": "x"}]}, "chapters[0].start: String should match"),
        ("release.json", {"approved_at": 1763460000}, "approved_at: Input should be a valid datetime"),
    ],
)
def test_schema_invalid_fails_on_a_top_level_field(episode, name, fields, expected):
    episode.update(name, **fields)
    problems = episode.only("SCHEMA_INVALID")
    assert any(p.message.startswith(expected) for p in problems), [p.line() for p in problems]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (b'{"schema_version": 1,', "not valid JSON:"),
        (b'{"schema_version": 1, "schema_version": 1}', "duplicate key 'schema_version' in a JSON object"),
        (b'{"loudness_lufs": NaN}', "NaN is not valid JSON"),
        (b"\xef\xbb\xbf{}", "the file starts with a UTF-8 byte order mark"),
        (b"\xff{}", "the file is not valid UTF-8"),
        (b"[]", "(file): Input should be an object"),
    ],
)
def test_schema_invalid_fails_for_a_file_that_is_not_clean_json(episode, raw, expected):
    episode.path("release.json").write_bytes(raw)
    problems = episode.only("SCHEMA_INVALID")
    assert any(p.message.startswith(expected) for p in problems), [p.line() for p in problems]


# DUPLICATE_ID


def test_duplicate_id_passes_when_ids_are_unique(episode):
    episode.passes()


@pytest.mark.parametrize(
    ("name", "list_field", "item_id"),
    [
        ("sources.json", "sources", "SRC-004"),
        ("claims.json", "claims", "CLM-005"),
        ("script.json", "segments", "SEG-001"),
        ("scenes.json", "scenes", "SCN-004"),
        ("assets.json", "assets", "AST-003"),
    ],
)
def test_duplicate_id_fails_when_an_id_repeats(episode, name, list_field, item_id):
    data = episode.load(name)
    data[list_field].append(next(dict(entry) for entry in data[list_field] if item_id in entry.values()))
    episode.save(name, data)
    problems = episode.only("DUPLICATE_ID")
    assert [(p.file, p.item_id) for p in problems] == [(name, item_id)]


# RETRY_LIMIT_EXCEEDED


def test_retry_limit_exceeded_passes_at_two_retries(episode):
    assert episode.load("episode.json")["stages"]["sources"]["retries"] == 2
    episode.passes()


def test_retry_limit_exceeded_passes_when_a_failed_stage_halts_the_episode(episode):
    def fail_script_stage(data):
        data["stages"]["script"] = {"status": "failed", "retries": 2, "last_error": "invented failure"}
        data["status"] = "halted_failure"

    episode.edit("episode.json", fail_script_stage)
    episode.passes()


def test_retry_limit_exceeded_fails_with_three_retries(episode):
    episode.edit("episode.json", lambda data: data["stages"]["script"].update(retries=3))
    problems = episode.only("RETRY_LIMIT_EXCEEDED")
    assert [p.message for p in problems] == ["stage script has 3 retries; the limit is 2"]


def test_retry_limit_exceeded_fails_when_a_failed_stage_does_not_halt(episode):
    episode.edit("episode.json", lambda data: data["stages"]["script"].update(status="failed", retries=2))
    problems = episode.only("RETRY_LIMIT_EXCEEDED")
    assert "not halted_failure" in problems[0].message


# BUDGET_CAP_EXCEEDED


def _set_costs(episode, status="active", **costs):
    def change(data):
        data["cost_usd"] = {"model": 0.0, "voice": 0.0, "assets": 0.0, "other": 0.0, **costs}
        data["status"] = status

    episode.edit("episode.json", change)


def test_budget_cap_exceeded_passes_just_below_the_cap(episode):
    _set_costs(episode, model=4.99, voice=5.0)
    episode.passes()


def test_budget_cap_exceeded_passes_when_halted_for_budget(episode):
    _set_costs(episode, status="halted_budget", model=12.0)
    episode.passes()


@pytest.mark.parametrize(
    "costs",
    [{"model": 10.0}, {"model": 6.0, "voice": 2.5, "assets": 1.0, "other": 0.5}, {"model": 11.5}],
)
def test_budget_cap_exceeded_fails_at_or_above_the_cap(episode, costs):
    _set_costs(episode, **costs)
    episode.only("BUDGET_CAP_EXCEEDED")


# SOURCE_FILE_MISSING


def test_source_file_missing_passes_when_files_exist(episode):
    episode.passes()


@pytest.mark.parametrize("relative", ["sources/SRC-002.pdf", "sources/SRC-002.txt"])
def test_source_file_missing_fails_when_a_file_is_deleted(episode, relative):
    episode.path(relative).unlink()
    problems = episode.only("SOURCE_FILE_MISSING")
    assert [(p.item_id, p.message.endswith(f"{relative} does not exist")) for p in problems] == [("SRC-002", True)]


def test_source_file_missing_probe_refuses_paths_outside_the_episode_folder(episode):
    (episode.root.parent / "outside.txt").write_text("not part of the episode", encoding="utf-8")
    fact = probe(episode.root, "../outside.txt")
    assert (fact.ok, fact.detail, fact.sha256) == (False, "is outside the episode folder", None)


# SOURCE_HASH_MISMATCH


def test_source_hash_mismatch_passes_when_hashes_match(episode):
    episode.passes()


def test_source_hash_mismatch_fails_when_a_saved_copy_changes(episode):
    episode.path("sources/SRC-003.pdf").write_bytes(b"changed")
    problems = episode.only("SOURCE_HASH_MISMATCH")
    assert [(p.item_id, p.message.startswith("sha256 does not match local_path")) for p in problems] == [
        ("SRC-003", True)
    ]


def test_source_hash_mismatch_fails_when_the_text_changes(episode):
    text_file = episode.path("sources/SRC-004.txt")
    text_file.write_bytes(text_file.read_bytes() + b"An appended line.\n")
    problems = episode.only("SOURCE_HASH_MISMATCH")
    assert problems[0].message.startswith("text_sha256 does not match text_path")


# INSUFFICIENT_SOURCES


def test_insufficient_sources_passes_with_two_of_each_tier(episode):
    episode.passes()


def test_insufficient_sources_passes_without_a_script(episode):
    episode.update("sources.json", "SRC-002", tier="scholarly")
    episode.path("script.json").unlink()
    episode.passes()


@pytest.mark.parametrize(("source_id", "tier"), [("SRC-002", "scholarly"), ("SRC-003", "primary")])
def test_insufficient_sources_fails_with_one_source_in_a_tier(episode, source_id, tier):
    episode.update("sources.json", source_id, tier=tier)
    episode.only("INSUFFICIENT_SOURCES")


# UNKNOWN_SOURCE


def test_unknown_source_passes_when_every_source_is_known(episode):
    episode.passes()


def test_unknown_source_fails_for_a_source_not_in_sources_json(episode):
    episode.update("claims.json", "CLM-002", source_id="SRC-009")
    problems = episode.only("UNKNOWN_SOURCE")
    assert [(p.item_id, p.message) for p in problems] == [("CLM-002", "source_id SRC-009 is not in sources.json")]


# QUOTE_NOT_FOUND


def test_quote_not_found_passes_despite_curly_quotes_hyphenation_and_spacing(episode):
    # CLM-001 has straight quotes and single spaces; the source has curly quotes and extra
    # spaces. CLM-005 reads "well-known"; the source breaks the line after "well-".
    episode.passes()


def test_quote_not_found_passes_for_a_superscript_quoted_as_written(episode):
    episode.update("claims.json", "CLM-005", quote="The floe lay 10² yards off the bow.")
    episode.passes()


def test_quote_not_found_fails_when_one_word_changes(episode):
    episode.update("claims.json", "CLM-002", quote="the steamer Example arrived at 4:25 a.m.")
    problems = episode.only("QUOTE_NOT_FOUND")
    assert [(p.item_id, p.message) for p in problems] == [("CLM-002", "quote not found in sources/SRC-002.txt (SRC-002)")]


def test_quote_not_found_fails_for_102_against_a_source_with_10_squared(episode):
    episode.update("claims.json", "CLM-005", quote="The floe lay 102 yards off the bow.")
    assert [p.item_id for p in episode.only("QUOTE_NOT_FOUND")] == ["CLM-005"]


def test_quote_not_found_fails_when_the_source_text_is_not_utf8(episode):
    text_file = episode.path("sources/SRC-002.txt")
    text_file.write_bytes(b"\xff\xfe not UTF-8")
    episode.update("sources.json", "SRC-002", text_sha256=probe(episode.root, "sources/SRC-002.txt").sha256)
    problems = episode.only("QUOTE_NOT_FOUND")
    assert "is not valid UTF-8" in problems[0].message


# LONE_CONFLICT_GROUP


def test_lone_conflict_group_passes_with_two_claims_in_the_group(episode):
    episode.passes()


def test_lone_conflict_group_fails_with_one_claim_in_the_group(episode):
    episode.update("claims.json", "CLM-004", conflict_group=None)
    problems = episode.only("LONE_CONFLICT_GROUP")
    assert [(p.item_id, p.message) for p in problems] == [
        ("CG-001", "conflict group CG-001 has only 1 claim (CLM-003); a group needs at least 2")
    ]


# UNKNOWN_CLAIM


def test_unknown_claim_passes_when_every_claim_is_known(episode):
    episode.passes()


def test_unknown_claim_fails_for_a_claim_not_in_claims_json(episode):
    episode.update("script.json", "SEG-004", claim_ids=["CLM-003", "CLM-004", "CLM-009"])
    episode.rehash("SEG-004")
    problems = episode.only("UNKNOWN_CLAIM")
    assert [(p.item_id, p.message) for p in problems] == [("SEG-004", "claim CLM-009 is not in claims.json")]


# UNCITED_FACTUAL_SEGMENT


def test_uncited_factual_segment_passes_for_uncited_narration(episode):
    episode.passes()  # SEG-001 cites nothing and is not factual


def test_uncited_factual_segment_fails_when_a_factual_segment_cites_nothing(episode):
    episode.update("script.json", "SEG-001", is_factual=True)
    assert [p.item_id for p in episode.only("UNCITED_FACTUAL_SEGMENT")] == ["SEG-001"]


# QUOTE_MISMATCH


def test_quote_mismatch_passes_when_the_quote_matches_after_normalization(episode):
    episode.passes()  # SEG-003 has curly quotes; CLM-001's quote has straight ones


def test_quote_mismatch_fails_when_one_word_differs(episode):
    episode.update("script.json", "SEG-003", text="I reported “ice astern” to the bridge")
    episode.rehash("SEG-003", reverify=True)
    problems = episode.only("QUOTE_MISMATCH")
    assert [(p.item_id, p.message) for p in problems] == [("SEG-003", "text does not match the quote of CLM-001")]


def test_quote_mismatch_fails_when_a_quote_cites_two_claims(episode):
    episode.update("script.json", "SEG-003", claim_ids=["CLM-001", "CLM-002"])
    episode.rehash("SEG-003", reverify=True)
    problems = episode.only("QUOTE_MISMATCH")
    assert "cites 2 claims; it must cite exactly one" in problems[0].message


# QUOTE_VOICE_MISMATCH


def test_quote_voice_mismatch_passes_when_quotes_use_the_quote_voice(episode):
    episode.passes()


def test_quote_voice_mismatch_fails_when_a_quote_uses_the_narrator(episode):
    episode.update("script.json", "SEG-003", voice="narrator")
    problems = episode.only("QUOTE_VOICE_MISMATCH")
    assert [(p.item_id, p.message) for p in problems] == [("SEG-003", "is_quote is true but voice is narrator")]


def test_quote_voice_mismatch_fails_when_narration_uses_the_quote_voice(episode):
    episode.update("script.json", "SEG-002", voice="quote")
    problems = episode.only("QUOTE_VOICE_MISMATCH")
    assert [(p.item_id, p.message) for p in problems] == [("SEG-002", "voice is quote but is_quote is false")]


# TEXT_HASH_MISMATCH


def test_text_hash_mismatch_passes_when_text_changes_only_in_spacing_and_quote_style(episode):
    episode.update("script.json", "SEG-002", text="  The lookout called a warning   to the bridge.\n")
    episode.update("script.json", "SEG-003", text='I reported "ice ahead" to the bridge')
    episode.passes()


def test_text_hash_mismatch_passes_when_claim_order_changes(episode):
    episode.update("script.json", "SEG-004", claim_ids=["CLM-004", "CLM-003"])
    episode.passes()


def test_text_hash_mismatch_fails_when_the_text_changes(episode):
    episode.update("script.json", "SEG-004", text="Accounts agree on the time of the collision.")
    assert [p.item_id for p in episode.only("TEXT_HASH_MISMATCH")] == ["SEG-004"]


def test_text_hash_mismatch_fails_when_the_claims_change(episode):
    episode.update("script.json", "SEG-004", claim_ids=["CLM-003", "CLM-004", "CLM-002"])
    assert [p.item_id for p in episode.only("TEXT_HASH_MISMATCH")] == ["SEG-004"]


# STALE_VERIFICATION


def test_stale_verification_passes_when_the_verified_hash_matches(episode):
    episode.passes()


def test_stale_verification_fails_when_text_changes_after_verification(episode):
    episode.update("script.json", "SEG-002", text="The lookout shouted a warning to the bridge.")
    episode.rehash("SEG-002")
    problems = episode.only("STALE_VERIFICATION")
    assert [(p.item_id, p.message) for p in problems] == [
        ("SEG-002", "verification_status is passed but verified_hash does not match text_hash")
    ]


def test_stale_verification_fails_when_passed_without_a_verified_hash(episode):
    episode.update("script.json", "SEG-002", verified_hash=None)
    assert episode.only("STALE_VERIFICATION")[0].message.endswith("verified_hash is null")


# UNKNOWN_SEGMENT


def test_unknown_segment_passes_when_every_segment_exists(episode):
    episode.passes()


def test_unknown_segment_fails_for_a_segment_not_in_script_json(episode):
    episode.update("scenes.json", "SCN-004", segment_id="SEG-009")
    problems = episode.only("UNKNOWN_SEGMENT")
    assert [(p.item_id, p.message) for p in problems] == [("SCN-004", "segment_id SEG-009 is not in script.json")]


# SEGMENT_HASH_MISMATCH


def test_segment_hash_mismatch_passes_when_hashes_match(episode):
    episode.passes()


def test_segment_hash_mismatch_fails_when_the_scene_hash_is_stale(episode):
    episode.update("scenes.json", "SCN-004", segment_hash=ZERO_HASH)
    problems = episode.only("SEGMENT_HASH_MISMATCH")
    assert [(p.item_id, p.message) for p in problems] == [("SCN-004", "segment_hash does not match the text_hash of SEG-004")]


# STATIC_SHOT_TOO_LONG


def test_static_shot_too_long_passes_at_exactly_eight_seconds(episode):
    assert episode.load("scenes.json")["scenes"][2]["duration_s"] == 8.0
    episode.passes()


def test_static_shot_too_long_passes_for_a_long_animated_shot(episode):
    episode.update("scenes.json", "SCN-002", duration_s=30.0)
    episode.passes()


def test_static_shot_too_long_fails_above_eight_seconds(episode):
    episode.update("scenes.json", "SCN-003", duration_s=8.5)
    problems = episode.only("STATIC_SHOT_TOO_LONG")
    assert [(p.item_id, p.message) for p in problems] == [("SCN-003", "static shot lasts 8.5 s; the limit is 8 s")]


# UNKNOWN_ASSET


def test_unknown_asset_passes_when_every_asset_exists(episode):
    episode.passes()


def test_unknown_asset_fails_for_an_asset_not_in_assets_json(episode):
    episode.update("scenes.json", "SCN-002", asset_ids=["AST-009"])
    problems = episode.only("UNKNOWN_ASSET")
    assert [(p.item_id, p.message) for p in problems] == [("SCN-002", "asset AST-009 is not in assets.json")]


# ASSET_FILE_MISSING


def test_asset_file_missing_passes_when_files_exist(episode):
    episode.passes()


def test_asset_file_missing_fails_when_a_file_is_deleted(episode):
    episode.path("assets/AST-001.png").unlink()
    problems = episode.only("ASSET_FILE_MISSING")
    assert [(p.item_id, p.message) for p in problems] == [("AST-001", "path assets/AST-001.png does not exist")]


# ASSET_HASH_MISMATCH


def test_asset_hash_mismatch_passes_when_hashes_match(episode):
    episode.passes()


def test_asset_hash_mismatch_fails_when_a_file_changes(episode):
    episode.path("assets/AST-002.png").write_bytes(b"a different image")
    assert [p.item_id for p in episode.only("ASSET_HASH_MISMATCH")] == ["AST-002"]


# ASSET_RIGHTS_UNRESOLVED


def test_asset_rights_unresolved_passes_for_an_unresolved_asset_no_scene_uses(episode):
    assert episode.load("assets.json")["assets"][2]["rights_status"] == "unresolved"  # AST-003, unused
    episode.passes()


@pytest.mark.parametrize("status", ["unresolved", "missing"])
def test_asset_rights_unresolved_fails_for_an_asset_a_scene_uses(episode, status):
    episode.update("assets.json", "AST-001", rights_status=status)
    problems = episode.only("ASSET_RIGHTS_UNRESOLVED")
    assert [(p.file, p.item_id, p.message) for p in problems] == [
        ("assets.json", "AST-001", f"rights_status is {status} but the asset is used by SCN-002")
    ]


def test_asset_rights_unresolved_fails_when_a_scene_starts_using_an_unresolved_asset(episode):
    episode.update("scenes.json", "SCN-004", asset_ids=["AST-003"])
    assert [p.item_id for p in episode.only("ASSET_RIGHTS_UNRESOLVED")] == ["AST-003"]


# UPLOAD_WITHOUT_APPROVAL

APPROVED_UPLOAD = {
    "youtube_id": "invented-video-id",
    "approver": "Test Owner",
    "approved_at": "2026-11-18T12:00:00Z",
    "video_sha256": ZERO_HASH,
    "qa": {"hard_failures": 0, "warnings": 2, "report_path": "qa/report.json"},
}


def test_upload_without_approval_passes_before_upload(episode):
    episode.passes()


def test_upload_without_approval_passes_with_full_approval(episode):
    episode.update("release.json", **APPROVED_UPLOAD)
    episode.passes()


@pytest.mark.parametrize("missing", ["approver", "approved_at", "video_sha256", "qa"])
def test_upload_without_approval_fails_when_a_field_is_missing(episode, missing):
    episode.update("release.json", **{**APPROVED_UPLOAD, missing: None})
    problems = episode.only("UPLOAD_WITHOUT_APPROVAL")
    assert [p.message for p in problems] == [f"youtube_id is set but {missing} missing"]


def test_upload_without_approval_fails_with_a_blank_approver(episode):
    episode.update("release.json", **{**APPROVED_UPLOAD, "approver": "  "})
    episode.only("UPLOAD_WITHOUT_APPROVAL")


def test_upload_without_approval_fails_with_qa_hard_failures(episode):
    episode.update("release.json", **{**APPROVED_UPLOAD, "qa": {**APPROVED_UPLOAD["qa"], "hard_failures": 1}})
    problems = episode.only("UPLOAD_WITHOUT_APPROVAL")
    assert [p.message for p in problems] == ["youtube_id is set but qa.hard_failures is 1"]


# CHAPTERS_INVALID


def _set_chapters(episode, *starts):
    episode.update("release.json", chapters=[{"start": start, "title": f"Chapter at {start}"} for start in starts])


def test_chapters_invalid_passes_for_valid_chapters(episode):
    episode.passes()


def test_chapters_invalid_passes_without_chapters(episode):
    _set_chapters(episode)
    episode.passes()


def test_chapters_invalid_passes_at_exactly_ten_seconds_apart(episode):
    _set_chapters(episode, "0:00", "0:10", "0:20", "1:00:00")
    episode.passes()


@pytest.mark.parametrize(
    ("starts", "expected"),
    [
        (("0:05", "0:45", "2:30"), ["the first chapter starts at 0:05, not 0:00"]),
        (("0:00", "0:45"), ["the chapter count is 2; at least 3 are required"]),
        (("0:00", "0:09", "2:30"), ["chapters at 0:00 and 0:09 are 9 s apart; the minimum is 10 s"]),
        (("0:00", "2:30", "0:45"), ["chapters at 2:30 and 0:45 are -105 s apart; the minimum is 10 s"]),
    ],
)
def test_chapters_invalid_fails(episode, starts, expected):
    _set_chapters(episode, *starts)
    assert [p.message for p in episode.only("CHAPTERS_INVALID")] == expected


# The validator only reads.


def test_validator_only_reads_files_and_makes_no_network_calls(episode, monkeypatch):
    episode.update("scenes.json", "SCN-003", duration_s=9.0)
    episode.path("assets/AST-001.png").unlink()

    def snapshot():
        return {
            path.relative_to(episode.root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in sorted(episode.root.rglob("*"))
            if path.is_file()
        }

    def refuse_network(*args, **kwargs):
        raise AssertionError("the validator tried to open a network connection")

    before = snapshot()
    monkeypatch.setattr(socket, "socket", refuse_network)
    monkeypatch.setattr(socket, "create_connection", refuse_network)
    codes = [p.code for p in validate_folder(episode.root).problems]
    assert codes == ["STATIC_SHOT_TOO_LONG", "ASSET_FILE_MISSING"]
    assert snapshot() == before
