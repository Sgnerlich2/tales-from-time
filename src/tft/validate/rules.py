"""Value and cross-file rules, as pure functions.

Each rule takes parsed contract models (and, for file rules, facts the runner gathered)
and returns its problems; an empty list means the rule passes. Rules never read or write
files themselves. Where another rule already reports the root cause (an unknown ID or a
missing file), a rule skips that entry instead of reporting it twice.
"""

import math
from collections import Counter, defaultdict
from collections.abc import Mapping

from pydantic import BaseModel

from tft.contracts.assets import Assets
from tft.contracts.claims import Claims
from tft.contracts.episode import Episode
from tft.contracts.release import Release, chapter_seconds
from tft.contracts.scenes import Scenes
from tft.contracts.script import Script
from tft.contracts.sources import Sources
from tft.textnorm import NormalizedText, normalize_quote, segment_hash
from tft.validate.files import FileFact
from tft.validate.loading import ID_FIELDS
from tft.validate.problems import Problem

RETRY_LIMIT = 2
STATIC_SHOT_LIMIT_S = 8.0
MIN_SOURCES_PER_TIER = 2
MIN_CHAPTERS = 3
MIN_CHAPTER_GAP_S = 10

# The contract files each file needs before it, following the stage order in episode.json
# (sources, claims, script, visuals for scenes.json, assets, then package for release.json).
# episode.json comes first of all and has its own rule, EPISODE_FILE_MISSING (IC23).
UPSTREAM_FILES: dict[str, tuple[str, ...]] = {
    "sources": (),
    "claims": ("sources",),
    "script": ("sources", "claims"),
    "scenes": ("sources", "claims", "script"),
    "assets": ("sources", "claims", "script", "scenes"),
    "release": ("sources", "claims", "script", "scenes", "assets"),
}


def episode_file_missing(present: frozenset[str]) -> list[Problem]:
    """EPISODE_FILE_MISSING: the episode folder has no episode.json (D20)."""
    if "episode" in present:
        return []
    return [Problem("episode.json", "-", "EPISODE_FILE_MISSING", "the episode folder has no episode.json")]


def upstream_file_missing(present: frozenset[str]) -> list[Problem]:
    """UPSTREAM_FILE_MISSING: a contract file is present but a file before it in the stage
    order is missing (D20). One problem per present file and missing upstream file."""
    return [
        Problem(
            f"{contract}.json",
            "-",
            "UPSTREAM_FILE_MISSING",
            f"{contract}.json needs {upstream}.json, which is missing",
        )
        for contract, upstreams in UPSTREAM_FILES.items()
        if contract in present
        for upstream in upstreams
        if upstream not in present
    ]


def duplicate_ids(contract: str, model: BaseModel) -> list[Problem]:
    """DUPLICATE_ID: an ID repeats within a file. One problem per repeated ID."""
    if contract not in ID_FIELDS:
        return []
    list_field, id_field = ID_FIELDS[contract]
    counts = Counter(getattr(entry, id_field) for entry in getattr(model, list_field))
    return [
        Problem(f"{contract}.json", item_id, "DUPLICATE_ID", f"{id_field} {item_id} appears {count} times")
        for item_id, count in counts.items()
        if count > 1
    ]


def retry_limit_exceeded(episode: Episode) -> list[Problem]:
    """RETRY_LIMIT_EXCEEDED: a stage has more than 2 retries, or a stage failed after 2
    retries while the episode status is not halted_failure."""
    problems = []
    for stage, state in episode.stages.items():
        if state.retries > RETRY_LIMIT:
            problems.append(
                Problem(
                    "episode.json",
                    "-",
                    "RETRY_LIMIT_EXCEEDED",
                    f"stage {stage} has {state.retries} retries; the limit is {RETRY_LIMIT}",
                )
            )
        if state.status == "failed" and state.retries >= RETRY_LIMIT and episode.status != "halted_failure":
            problems.append(
                Problem(
                    "episode.json",
                    "-",
                    "RETRY_LIMIT_EXCEEDED",
                    f"stage {stage} failed after {state.retries} retries but the episode status is "
                    f"{episode.status}, not halted_failure",
                )
            )
    return problems


def budget_cap_exceeded(episode: Episode) -> list[Problem]:
    """BUDGET_CAP_EXCEEDED: total cost is at or above budget_cap_usd while the status is not
    halted_budget."""
    cost = episode.cost_usd
    total = math.fsum((cost.model, cost.voice, cost.assets, cost.other))
    if total >= episode.budget_cap_usd and episode.status != "halted_budget":
        return [
            Problem(
                "episode.json",
                "-",
                "BUDGET_CAP_EXCEEDED",
                f"total cost {total:.2f} USD is at or above the cap of {episode.budget_cap_usd:.2f} USD "
                f"but the status is {episode.status}, not halted_budget",
            )
        ]
    return []


def _source_files(sources: Sources):
    for source in sources.sources:
        yield source, "local_path", source.local_path, "sha256", source.sha256
        yield source, "text_path", source.text_path, "text_sha256", source.text_sha256


def source_file_missing(sources: Sources, files: Mapping[str, FileFact]) -> list[Problem]:
    """SOURCE_FILE_MISSING: local_path or text_path does not exist."""
    return [
        Problem("sources.json", source.source_id, "SOURCE_FILE_MISSING", f"{field} {path} {files[path].detail}")
        for source, field, path, _, _ in _source_files(sources)
        if not files[path].ok
    ]


def source_hash_mismatch(sources: Sources, files: Mapping[str, FileFact]) -> list[Problem]:
    """SOURCE_HASH_MISMATCH: a file's SHA-256 differs from the recorded one."""
    return [
        Problem(
            "sources.json",
            source.source_id,
            "SOURCE_HASH_MISMATCH",
            f"{hash_field} does not match {field} {path}, whose SHA-256 is {files[path].sha256}",
        )
        for source, field, path, hash_field, recorded in _source_files(sources)
        if files[path].ok and files[path].sha256 != recorded
    ]


def insufficient_sources(sources: Sources, script_present: bool) -> list[Problem]:
    """INSUFFICIENT_SOURCES: script.json exists and there are fewer than 2 primary or fewer
    than 2 scholarly sources. Sources are counted by distinct source_id."""
    if not script_present:
        return []
    primary = {s.source_id for s in sources.sources if s.tier == "primary"}
    scholarly = {s.source_id for s in sources.sources if s.tier == "scholarly"}
    if len(primary) >= MIN_SOURCES_PER_TIER and len(scholarly) >= MIN_SOURCES_PER_TIER:
        return []
    return [
        Problem(
            "sources.json",
            "-",
            "INSUFFICIENT_SOURCES",
            f"script.json exists but there are {len(primary)} primary and {len(scholarly)} scholarly "
            f"sources; at least {MIN_SOURCES_PER_TIER} of each are required",
        )
    ]


def unknown_source(claims: Claims, sources: Sources) -> list[Problem]:
    """UNKNOWN_SOURCE: source_id is not in sources.json. Rejected claims are skipped (D18)."""
    known = {s.source_id for s in sources.sources}
    return [
        Problem("claims.json", c.claim_id, "UNKNOWN_SOURCE", f"source_id {c.source_id} is not in sources.json")
        for c in claims.claims
        if c.status != "rejected" and c.source_id not in known
    ]


def quote_not_found(
    claims: Claims,
    sources: Sources,
    files: Mapping[str, FileFact],
    texts: Mapping[str, str | None],
) -> list[Problem]:
    """QUOTE_NOT_FOUND: the normalized quote is not a substring of the normalized text_path
    file, checked with line-break hyphens joined and with them kept; either way passes.

    Rejected claims are skipped (D18). Claims with an unknown source or a missing text file
    are skipped too (UNKNOWN_SOURCE and SOURCE_FILE_MISSING report those). A text file that
    is not valid UTF-8 cannot be searched, so its claims fail.
    """
    by_id = {s.source_id: s for s in sources.sources}
    haystacks: dict[str, NormalizedText] = {}
    problems = []
    for claim in claims.claims:
        if claim.status == "rejected":
            continue
        source = by_id.get(claim.source_id)
        if source is None or not files[source.text_path].ok:
            continue
        text = texts.get(source.text_path)
        if text is None:
            problems.append(
                Problem(
                    "claims.json",
                    claim.claim_id,
                    "QUOTE_NOT_FOUND",
                    f"cannot search {source.text_path} ({source.source_id}): it is not valid UTF-8",
                )
            )
            continue
        if source.text_path not in haystacks:
            haystacks[source.text_path] = NormalizedText(text)
        if not haystacks[source.text_path].contains(claim.quote):
            problems.append(
                Problem(
                    "claims.json",
                    claim.claim_id,
                    "QUOTE_NOT_FOUND",
                    f"quote not found in {source.text_path} ({source.source_id})",
                )
            )
    return problems


def lone_conflict_group(claims: Claims) -> list[Problem]:
    """LONE_CONFLICT_GROUP: a conflict group has fewer than 2 claims. Rejected claims are
    skipped and do not count toward a group's two (D18)."""
    members: dict[str, list[str]] = defaultdict(list)
    for claim in claims.claims:
        if claim.status == "rejected" or claim.conflict_group is None:
            continue
        if claim.claim_id not in members[claim.conflict_group]:
            members[claim.conflict_group].append(claim.claim_id)
    return [
        Problem(
            "claims.json",
            group,
            "LONE_CONFLICT_GROUP",
            f"conflict group {group} has only {len(ids)} claim ({', '.join(ids)}); a group needs at least 2",
        )
        for group, ids in members.items()
        if len(ids) < 2
    ]


def unknown_claim(script: Script, claims: Claims) -> list[Problem]:
    """UNKNOWN_CLAIM: a claim ID is not in claims.json."""
    known = {c.claim_id for c in claims.claims}
    return [
        Problem("script.json", segment.segment_id, "UNKNOWN_CLAIM", f"claim {claim_id} is not in claims.json")
        for segment in script.segments
        for claim_id in segment.claim_ids
        if claim_id not in known
    ]


def rejected_claim_cited(script: Script, claims: Claims) -> list[Problem]:
    """REJECTED_CLAIM_CITED: a script segment cites a claim whose status is rejected (D18).
    Rejected claims stay in claims.json as a record, but nothing may cite them."""
    rejected = {c.claim_id for c in claims.claims if c.status == "rejected"}
    return [
        Problem("script.json", segment.segment_id, "REJECTED_CLAIM_CITED", f"cites {claim_id}, which is rejected")
        for segment in script.segments
        for claim_id in segment.claim_ids
        if claim_id in rejected
    ]


def uncited_factual_segment(script: Script) -> list[Problem]:
    """UNCITED_FACTUAL_SEGMENT: is_factual is true and claim_ids is empty."""
    return [
        Problem(
            "script.json",
            segment.segment_id,
            "UNCITED_FACTUAL_SEGMENT",
            "is_factual is true but claim_ids is empty",
        )
        for segment in script.segments
        if segment.is_factual and not segment.claim_ids
    ]


def quote_mismatch(script: Script, claims: Claims) -> list[Problem]:
    """QUOTE_MISMATCH: is_quote is true and the segment does not cite exactly one claim whose
    normalized quote equals the normalized segment text.

    A quote segment must cite exactly one claim, and that claim's quote must match. If the
    one cited claim is not in claims.json, UNKNOWN_CLAIM reports it instead.
    """
    by_id = {c.claim_id: c for c in claims.claims}
    problems = []
    for segment in script.segments:
        if not segment.is_quote:
            continue
        if len(segment.claim_ids) != 1:
            problems.append(
                Problem(
                    "script.json",
                    segment.segment_id,
                    "QUOTE_MISMATCH",
                    f"is_quote is true but the segment cites {len(segment.claim_ids)} claims; "
                    "it must cite exactly one",
                )
            )
            continue
        claim = by_id.get(segment.claim_ids[0])
        if claim is not None and normalize_quote(claim.quote) != normalize_quote(segment.text):
            problems.append(
                Problem(
                    "script.json",
                    segment.segment_id,
                    "QUOTE_MISMATCH",
                    f"text does not match the quote of {claim.claim_id}",
                )
            )
    return problems


def quote_voice_mismatch(script: Script) -> list[Problem]:
    """QUOTE_VOICE_MISMATCH: is_quote is true and voice is not quote, or voice is quote and
    is_quote is false."""
    problems = []
    for segment in script.segments:
        if segment.is_quote and segment.voice != "quote":
            message = f"is_quote is true but voice is {segment.voice}"
        elif segment.voice == "quote" and not segment.is_quote:
            message = "voice is quote but is_quote is false"
        else:
            continue
        problems.append(Problem("script.json", segment.segment_id, "QUOTE_VOICE_MISMATCH", message))
    return problems


def text_hash_mismatch(script: Script) -> list[Problem]:
    """TEXT_HASH_MISMATCH: text_hash differs from segment_hash(text, claim_ids)."""
    problems = []
    for segment in script.segments:
        expected = segment_hash(segment.text, segment.claim_ids)
        if segment.text_hash != expected:
            problems.append(
                Problem(
                    "script.json",
                    segment.segment_id,
                    "TEXT_HASH_MISMATCH",
                    f"text_hash does not match segment_hash(text, claim_ids), which is {expected}",
                )
            )
    return problems


def stale_verification(script: Script) -> list[Problem]:
    """STALE_VERIFICATION: verification_status is passed and verified_hash differs from text_hash."""
    return [
        Problem(
            "script.json",
            segment.segment_id,
            "STALE_VERIFICATION",
            "verification_status is passed but verified_hash "
            + ("is null" if segment.verified_hash is None else "does not match text_hash"),
        )
        for segment in script.segments
        if segment.verification_status == "passed" and segment.verified_hash != segment.text_hash
    ]


def unknown_segment(scenes: Scenes, script: Script) -> list[Problem]:
    """UNKNOWN_SEGMENT: segment_id is not in script.json."""
    known = {s.segment_id for s in script.segments}
    return [
        Problem("scenes.json", scene.scene_id, "UNKNOWN_SEGMENT", f"segment_id {scene.segment_id} is not in script.json")
        for scene in scenes.scenes
        if scene.segment_id not in known
    ]


def segment_hash_mismatch(scenes: Scenes, script: Script) -> list[Problem]:
    """SEGMENT_HASH_MISMATCH: segment_hash differs from that segment's text_hash.
    Scenes with an unknown segment are skipped (UNKNOWN_SEGMENT reports them)."""
    by_id = {s.segment_id: s for s in script.segments}
    return [
        Problem(
            "scenes.json",
            scene.scene_id,
            "SEGMENT_HASH_MISMATCH",
            f"segment_hash does not match the text_hash of {scene.segment_id}",
        )
        for scene in scenes.scenes
        if scene.segment_id in by_id and scene.segment_hash != by_id[scene.segment_id].text_hash
    ]


def static_shot_too_long(scenes: Scenes) -> list[Problem]:
    """STATIC_SHOT_TOO_LONG: motion is static and duration_s is above 8.0."""
    return [
        Problem(
            "scenes.json",
            scene.scene_id,
            "STATIC_SHOT_TOO_LONG",
            f"static shot lasts {scene.duration_s:g} s; the limit is {STATIC_SHOT_LIMIT_S:g} s",
        )
        for scene in scenes.scenes
        if scene.motion == "static" and scene.duration_s > STATIC_SHOT_LIMIT_S
    ]


def unknown_asset(scenes: Scenes, assets: Assets) -> list[Problem]:
    """UNKNOWN_ASSET: an asset ID is not in assets.json."""
    known = {a.asset_id for a in assets.assets}
    return [
        Problem("scenes.json", scene.scene_id, "UNKNOWN_ASSET", f"asset {asset_id} is not in assets.json")
        for scene in scenes.scenes
        for asset_id in scene.asset_ids
        if asset_id not in known
    ]


def asset_file_missing(assets: Assets, files: Mapping[str, FileFact]) -> list[Problem]:
    """ASSET_FILE_MISSING: path does not exist."""
    return [
        Problem("assets.json", asset.asset_id, "ASSET_FILE_MISSING", f"path {asset.path} {files[asset.path].detail}")
        for asset in assets.assets
        if not files[asset.path].ok
    ]


def asset_hash_mismatch(assets: Assets, files: Mapping[str, FileFact]) -> list[Problem]:
    """ASSET_HASH_MISMATCH: the file's SHA-256 differs from the recorded one."""
    return [
        Problem(
            "assets.json",
            asset.asset_id,
            "ASSET_HASH_MISMATCH",
            f"sha256 does not match path {asset.path}, whose SHA-256 is {files[asset.path].sha256}",
        )
        for asset in assets.assets
        if files[asset.path].ok and files[asset.path].sha256 != asset.sha256
    ]


def asset_rights_unresolved(assets: Assets, scenes: Scenes) -> list[Problem]:
    """ASSET_RIGHTS_UNRESOLVED: an asset used by any scene has rights_status other than
    cleared. Reported once per asset, on assets.json, naming the scenes that use it."""
    users: dict[str, list[str]] = defaultdict(list)
    for scene in scenes.scenes:
        for asset_id in scene.asset_ids:
            if scene.scene_id not in users[asset_id]:
                users[asset_id].append(scene.scene_id)
    problems = []
    for asset in assets.assets:
        if asset.rights_status != "cleared" and users.get(asset.asset_id):
            problems.append(
                Problem(
                    "assets.json",
                    asset.asset_id,
                    "ASSET_RIGHTS_UNRESOLVED",
                    f"rights_status is {asset.rights_status} but the asset is used by "
                    f"{', '.join(users[asset.asset_id])}",
                )
            )
    return problems


def upload_without_approval(release: Release) -> list[Problem]:
    """UPLOAD_WITHOUT_APPROVAL: youtube_id is set and approver, approved_at, video_sha256, or
    qa is missing, or qa.hard_failures is above 0. A blank approver counts as missing."""
    if release.youtube_id is None:
        return []
    required = {
        "approver": release.approver if release.approver and release.approver.strip() else None,
        "approved_at": release.approved_at,
        "video_sha256": release.video_sha256,
        "qa": release.qa,
    }
    reasons = []
    missing = [name for name, value in required.items() if value is None]
    if missing:
        reasons.append(f"{', '.join(missing)} missing")
    if release.qa is not None and release.qa.hard_failures > 0:
        reasons.append(f"qa.hard_failures is {release.qa.hard_failures}")
    if not reasons:
        return []
    return [Problem("release.json", "-", "UPLOAD_WITHOUT_APPROVAL", f"youtube_id is set but {'; '.join(reasons)}")]


def chapters_invalid(release: Release) -> list[Problem]:
    """CHAPTERS_INVALID: chapters exist and the first is not 0:00, there are fewer than 3, or
    two consecutive chapters are less than 10 seconds apart. One problem per finding."""
    chapters = release.chapters
    if not chapters:
        return []
    problems = []
    if chapter_seconds(chapters[0].start) != 0:
        problems.append(
            Problem("release.json", "-", "CHAPTERS_INVALID", f"the first chapter starts at {chapters[0].start}, not 0:00")
        )
    if len(chapters) < MIN_CHAPTERS:
        problems.append(
            Problem(
                "release.json",
                "-",
                "CHAPTERS_INVALID",
                f"the chapter count is {len(chapters)}; at least {MIN_CHAPTERS} are required",
            )
        )
    for earlier, later in zip(chapters, chapters[1:]):
        gap = chapter_seconds(later.start) - chapter_seconds(earlier.start)
        if gap < MIN_CHAPTER_GAP_S:
            problems.append(
                Problem(
                    "release.json",
                    "-",
                    "CHAPTERS_INVALID",
                    f"chapters at {earlier.start} and {later.start} are {gap} s apart; "
                    f"the minimum is {MIN_CHAPTER_GAP_S} s",
                )
            )
    return problems
