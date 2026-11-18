"""Shared fixture: an invented episode folder that passes every rule, with helpers to break it.

Every document here is invented for testing and labeled as such; none is real history (IC11).
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from tft.textnorm import file_sha256, segment_hash
from tft.validate import Problem, validate_folder

EPISODE_ID = "EP-0001"

SOURCE_TEXTS = {
    "SRC-001": (
        "INVENTED TEST DOCUMENT, not a real historical source.\n"
        "Deposition of the lookout, taken 3 May 1901.\n"
        "At 4:10 a.m. I reported “ice ahead” to   the bridge, and the well-\n"
        "known captain ordered the engines full astern.\n"
        "The floe lay 10² yards off the bow.\n"
    ),
    "SRC-002": (
        "INVENTED TEST DOCUMENT, not a real historical source.\n"
        "Harbour log, 3 May 1901: the steamer Example signalled at 4:25 a.m.\n"
    ),
    "SRC-003": "INVENTED TEST DOCUMENT, not real scholarship.\nThe inquiry put the collision at 4:12 a.m.\n",
    "SRC-004": "INVENTED TEST DOCUMENT, not real scholarship.\nA later study placed the collision nearer 4:20 a.m.\n",
}
SOURCE_TIERS = {"SRC-001": "primary", "SRC-002": "primary", "SRC-003": "scholarly", "SRC-004": "scholarly"}
SOURCE_DATES = {"SRC-001": "1901-05-03", "SRC-002": "1901-05", "SRC-003": "1902", "SRC-004": "1950-06-01"}
ASSET_RIGHTS = {"AST-001": "cleared", "AST-002": "cleared", "AST-003": "unresolved"}  # AST-003 is unused
ID_KEYS = ("source_id", "claim_id", "segment_id", "scene_id", "asset_id")


def write_json(path: Path, data: Any) -> None:
    path.write_bytes((json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def _write_files(root: Path) -> None:
    (root / "sources").mkdir(parents=True)
    (root / "assets").mkdir()
    for source_id, text in SOURCE_TEXTS.items():
        (root / "sources" / f"{source_id}.txt").write_bytes(text.encode("utf-8"))
        (root / "sources" / f"{source_id}.pdf").write_bytes(f"%PDF-1.4 invented test file {source_id}\n".encode())
    for asset_id in ASSET_RIGHTS:
        (root / "assets" / f"{asset_id}.png").write_bytes(f"invented test image {asset_id}\n".encode())


def _episode() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "episode_id": EPISODE_ID,
        "working_title": "Invented test episode: the lookout's warning",
        "current_stage": "script",
        "status": "active",
        "stages": {
            "topics": {"status": "done", "retries": 0, "last_error": None},
            "sources": {"status": "done", "retries": 2, "last_error": "invented transient error"},
            "claims": {"status": "done", "retries": 0},
            "script": {"status": "running", "retries": 1},
        },
        "gates": {
            "topic": {"state": "approved", "approver": "Test Owner", "decided_at": "2026-11-18T10:00:00Z"},
            "script": {"state": "pending"},
            "final": {"state": "pending", "approver": None, "decided_at": None},
        },
        "budget_cap_usd": 10.0,
        "cost_usd": {"model": 1.25, "voice": 0.0, "assets": 0.5, "other": 0.0},
        "error_log": [{"at": "2026-11-18T09:30:00Z", "stage": "sources", "message": "invented transient error"}],
    }


def _sources(root: Path) -> dict[str, Any]:
    entries = []
    for source_id, tier in SOURCE_TIERS.items():
        local_path, text_path = f"sources/{source_id}.pdf", f"sources/{source_id}.txt"
        entries.append(
            {
                "source_id": source_id,
                "title": f"Invented test document {source_id}",
                "author": "Invented author",
                "date": SOURCE_DATES[source_id],
                "tier": tier,
                "url": f"https://example.invalid/{source_id}",
                "local_path": local_path,
                "sha256": file_sha256(root / local_path),
                "text_path": text_path,
                "text_sha256": file_sha256(root / text_path),
                "retrieved": "2026-11-18",
                "bias_note": "Invented for tests: written by an interested party soon after the event.",
            }
        )
    return {"schema_version": 1, "episode_id": EPISODE_ID, "sources": entries}


def _claim(claim_id: str, source_id: str, quote: str, location: str, group: str | None = None) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "text": f"Invented claim {claim_id}.",
        "source_id": source_id,
        "location": location,
        "quote": quote,
        "evidence_strength": "moderate",
        "conflict_group": group,
        "status": "verified",
    }


def _claims() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "episode_id": EPISODE_ID,
        "claims": [
            # Straight quotes and single spaces, against curly quotes and extra spaces in the source.
            _claim("CLM-001", "SRC-001", 'I reported "ice ahead" to the bridge', "line 3"),
            _claim("CLM-002", "SRC-002", "the steamer Example signalled at 4:25 a.m.", "entry 1"),
            _claim("CLM-003", "SRC-003", "The inquiry put the collision at 4:12 a.m.", "p. 1", "CG-001"),
            _claim("CLM-004", "SRC-004", "A later study placed the collision nearer 4:20 a.m.", "p. 2", "CG-001"),
            # "well-" ends a line in the source and "known" starts the next.
            _claim("CLM-005", "SRC-001", "the well-known captain ordered the engines full astern", "lines 3 to 4"),
        ],
    }


def _segment(
    segment_id: str, act: int, text: str, claim_ids: list[str], factual: bool, quote: bool = False, passed: bool = False
) -> dict[str, Any]:
    text_hash = segment_hash(text, claim_ids)
    return {
        "segment_id": segment_id,
        "act": act,
        "text": text,
        "claim_ids": claim_ids,
        "is_factual": factual,
        "is_quote": quote,
        "voice": "quote" if quote else "narrator",
        "text_hash": text_hash,
        "verified_hash": text_hash if passed else None,
        "verification_status": "passed" if passed else "unverified",
    }


def _script() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "episode_id": EPISODE_ID,
        "angle": "Invented angle for tests.",
        "title_options": ["Invented title one", "Invented title two"],
        "target_words": 1150,
        "segments": [
            _segment("SEG-001", 1, "Before dawn, a lookout saw something in the water.", [], factual=False),
            _segment("SEG-002", 2, "The lookout called a warning to the bridge.", ["CLM-001"], True, passed=True),
            _segment("SEG-003", 3, "I reported “ice ahead” to the bridge", ["CLM-001"], True, True, True),
            _segment("SEG-004", 4, "Accounts differ on the time of the collision.", ["CLM-003", "CLM-004"], True),
        ],
    }


def _scene(
    scene_id: str,
    segment: dict[str, Any],
    component: str,
    start: float,
    duration: float,
    motion: str,
    asset_ids: list[str] | None = None,
    citation: str | None = None,
) -> dict[str, Any]:
    return {
        "scene_id": scene_id,
        "segment_id": segment["segment_id"],
        "segment_hash": segment["text_hash"],
        "component": component,
        "props": {"label": f"invented props for {scene_id}"},
        "asset_ids": asset_ids or [],
        "citation": citation,
        "motion": motion,
        "start_s": start,
        "duration_s": duration,
    }


def _scenes(script: dict[str, Any]) -> dict[str, Any]:
    seg = {s["segment_id"]: s for s in script["segments"]}
    return {
        "schema_version": 1,
        "episode_id": EPISODE_ID,
        "scenes": [
            _scene("SCN-001", seg["SEG-001"], "chapter_card", 0.0, 4.0, "static"),
            _scene("SCN-002", seg["SEG-002"], "map_zoom", 4.0, 12.0, "animated", ["AST-001"]),
            # A static shot of exactly 8.0 seconds is at the limit and passes.
            _scene("SCN-003", seg["SEG-003"], "document_quote", 16.0, 8.0, "static", ["AST-002"], "Invented deposition"),
            _scene("SCN-004", seg["SEG-004"], "timeline", 24.0, 10.0, "animated"),
        ],
    }


def _assets(root: Path) -> dict[str, Any]:
    entries = []
    for asset_id, rights in ASSET_RIGHTS.items():
        path = f"assets/{asset_id}.png"
        entries.append(
            {
                "asset_id": asset_id,
                "path": path,
                "sha256": file_sha256(root / path),
                "kind": "image",
                "source_url": f"https://example.invalid/{asset_id}",
                "creator": "Invented creator",
                "archive": "Invented archive",
                "date": "1901",
                "original_status": "public_domain",
                "reproduction_license": "none required",
                "attribution": "Invented archive, test image",
                "rights_status": rights,
            }
        )
    return {"schema_version": 1, "episode_id": EPISODE_ID, "assets": entries}


def _release() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "episode_id": EPISODE_ID,
        "video_sha256": None,
        "loudness_lufs": None,
        "true_peak_dbtp": None,
        "qa": None,
        "title": "Invented test episode",
        "description": "Invented description. Narration uses AI-generated voices.",
        "chapters": [
            {"start": "0:00", "title": "The anomaly"},
            {"start": "0:45", "title": "The constraints"},
            {"start": "2:30", "title": "The friction"},
        ],
        "captions_sha256": None,
        "synthetic_disclosure": True,
        "visibility": "private",
        "approver": None,
        "approved_at": None,
        "youtube_id": None,
    }


def _entry(data: dict[str, Any], item_id: str) -> dict[str, Any]:
    for value in data.values():
        if isinstance(value, list):
            for entry in value:
                if isinstance(entry, dict) and any(entry.get(key) == item_id for key in ID_KEYS):
                    return entry
    raise KeyError(item_id)


class EpisodeFolder:
    """An invented episode folder in tmp_path, with helpers to change and validate it."""

    def __init__(self, root: Path) -> None:
        self.root = root
        _write_files(root)
        script = _script()
        contents = {
            "episode.json": _episode(),
            "sources.json": _sources(root),
            "claims.json": _claims(),
            "script.json": script,
            "scenes.json": _scenes(script),
            "assets.json": _assets(root),
            "release.json": _release(),
        }
        for name, data in contents.items():
            write_json(root / name, data)

    def path(self, relative: str) -> Path:
        return self.root / relative

    def load(self, name: str) -> dict[str, Any]:
        return json.loads(self.path(name).read_text(encoding="utf-8"))

    def save(self, name: str, data: dict[str, Any]) -> None:
        write_json(self.path(name), data)

    def edit(self, name: str, change: Callable[[dict[str, Any]], Any]) -> None:
        data = self.load(name)
        change(data)
        self.save(name, data)

    def update(self, name: str, item_id: str | None = None, **fields: Any) -> None:
        """Set fields on the file's top level, or on the list entry with this ID."""
        data = self.load(name)
        (data if item_id is None else _entry(data, item_id)).update(fields)
        self.save(name, data)

    def rehash(self, segment_id: str, reverify: bool = False) -> None:
        """After changing a segment, recompute its text_hash and its scenes' segment_hash.
        With reverify, also record the new hash as verified."""
        script = self.load("script.json")
        segment = _entry(script, segment_id)
        segment["text_hash"] = segment_hash(segment["text"], segment["claim_ids"])
        if reverify:
            segment["verified_hash"] = segment["text_hash"]
        self.save("script.json", script)
        scenes = self.load("scenes.json")
        for scene in scenes["scenes"]:
            if scene["segment_id"] == segment_id:
                scene["segment_hash"] = segment["text_hash"]
        self.save("scenes.json", scenes)

    def problems(self) -> list[Problem]:
        return validate_folder(self.root).problems

    def codes(self) -> list[str]:
        return [problem.code for problem in self.problems()]

    def passes(self) -> None:
        """Assert the whole folder validates with no problems."""
        assert [problem.line() for problem in self.problems()] == []

    def only(self, code: str) -> list[Problem]:
        """Assert validation reports this code and no other; return those problems."""
        problems = self.problems()
        assert problems and {problem.code for problem in problems} == {code}, [p.line() for p in problems]
        return problems


@pytest.fixture
def episode(tmp_path: Path) -> EpisodeFolder:
    return EpisodeFolder(tmp_path / EPISODE_ID)
