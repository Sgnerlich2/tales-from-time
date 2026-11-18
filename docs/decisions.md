# Decisions

Rules for editing this log are in CLAUDE.md under Records.

| ID | Decision | Status |
| --- | --- | --- |
| D1 | ElevenLabs voices, not Steven's: a narrator and a separate quote reader | Owner confirmed |
| D2 | Automate every routine stage; Steven handles topic choice, final review, exceptions | Owner confirmed |
| D3 | Production machine Ryzen 5 3600, 32 GB RAM, RX 580 8 GB, 1 TB SSD; no CUDA | Owner confirmed |
| D4 | Role chain Pre-Architect, Duet, Claude Code, pipeline; Steven final authority | Owner confirmed |
| D5 | Remotion renders the finished video; no external editor | Recommended |
| D6 | Scope 1600 to 1930; three formats; exclude atrocities, contested religious history, current geopolitics | Recommended |
| D7 | Pipeline finds sources and extracts claims; Steven does not curate | Recommended |
| D8 | Quotes must match the saved source word for word; model support check can block, never certify | Recommended |
| D9 | One orchestrator calling stateless, schema-bound model steps; no agent chat | Recommended |
| D10 | Local-first: files plus Git; cloud only for model, voice, backup APIs | Recommended |
| D11 | Pipeline uploads as private at most; Steven publishes | Recommended |
| D12 | Visuals: public-domain archival images, maps, diagrams, timelines, document callouts | Recommended |
| D13 | Workspace on a 1 to 2 TB external SSD; finished episodes archived to cloud | Deferred by Steven, Nov 1, 2026: pilot runs on the internal 1 TB SSD (about 320 GB free); buy the external SSD after the first few episodes |
| D14 | Upgrade the desktop to Windows 11 before API keys go on it | Owner confirmed (Nov 1, 2026) |
| D15 | Keys in a git-ignored .env, one per service, provider spend limits | Recommended |
| D16 | About $150 per month cash; $10 variable cap per episode | Owner confirmed (Nov 1, 2026) |
| D17 | tft validate on one contract file runs SCHEMA_INVALID, DUPLICATE_ID, and every other rule that needs only that file; rules that need another file, or files on disk, run only in folder mode | Owner confirmed (Nov 18, 2026) |
| D18 | Rejected claims stay in claims.json as a record. QUOTE_NOT_FOUND, UNKNOWN_SOURCE, and LONE_CONFLICT_GROUP skip them, and a rejected claim does not count toward a group's two. New rule REJECTED_CLAIM_CITED: a script segment that cites a rejected claim fails | Owner confirmed (Nov 18, 2026) |
| D19 | normalize_quote also maps U+2010, U+2011, U+2012, and U+2015 to a plain hyphen. A line-break hyphen between digits stays unjoined, since it is often a range. QUOTE_MISMATCH is unchanged | Owner confirmed (Nov 18, 2026) |
| D20 | Folder validation fails without episode.json (EPISODE_FILE_MISSING), and a contract file whose upstream file is missing fails with UPSTREAM_FILE_MISSING, naming both files. Upstream follows the stage order the contracts imply (map in IC23) | Owner confirmed (Nov 18, 2026) |
| D21 | claims.location must be non-empty, per CHARTER.md | Owner confirmed (Nov 18, 2026) |
| D22 | schema_version stays 1 for the M0.2 contracts; standing rule 4 (bump on contract change) applies from the first contract change after M0.2 merges | Owner confirmed (Nov 18, 2026) |
| IC1 | Python 3.12 for orchestrator and checks; TypeScript for Remotion | Implementation choice |
| IC2 | uv for Python, environment, and lockfile; pytest; Typer CLI | Implementation choice |
| IC3 | Pydantic v2 models are the contracts; JSON Schema exported for TypeScript | Implementation choice |
| IC4 | Python side in native Windows PowerShell, no WSL2; Remotion platform decided at E1 | Implementation choice |
| IC5 | Episode workspace at TFT_WORKSPACE outside the repo, default C:\tft-workspace on the internal drive; moving to the external SSD later is only a change of TFT_WORKSPACE; workspace/ is the git-ignored fallback, used only when TFT_WORKSPACE is empty | Implementation choice |
| IC6 | Integer schema_version in every contract file, starting at 1 | Implementation choice |
| IC7 | ID formats EP-0001, SRC-001, CLM-001, SEG-001, SCN-001, AST-001, CG-001 | Implementation choice |
| IC8 | Quote normalization: straight quotes, dashes to hyphen, ellipsis to three dots, line-break hyphenation joined, whitespace collapsed; no NFKC or other Unicode normalization, so the charter's word-for-word rule holds (for example 10² never matches 102) | Implementation choice |
| IC9 | Segment hash: SHA-256 of normalized text, newline, sorted claim IDs joined by commas | Implementation choice |
| IC10 | JSON paths relative with forward slashes; text UTF-8 with LF via .gitattributes | Implementation choice |
| IC11 | Golden fixture uses invented, labeled documents, never real history | Implementation choice |
| IC12 | Channel index is a JSON file at launch; revisit SQLite at Phase 4 | Implementation choice |
| IC13 | Stage names follow the handoff's 11 components; 9-stage grouping to confirm | Implementation choice |
| IC14 | Drive mirrors docs and the finished-episode archive, one way from repo to Drive | Implementation choice |
| IC15 | Model calls go through one adapter that runs Claude Code headless on Steven's Claude plan, using the strongest model for each step; Anthropic API is a fallback behind the same adapter, drawing on the $200 of API credits in Steven's Claude plan, with the adapter's API spend cap kept well below that (suggested $50 per month). The adapter logs model, tokens and estimated cost per call; plan usage limits pause the run, which resumes later | Implementation choice |
| IC16 | Build backend uv_build (uv's own backend and its default for new packages) builds package tft from src/tft and installs the tft console script; build-time only, adds no runtime dependency | Implementation choice |
| IC17 | Contract models use Pydantic strict mode: no type coercion (a "1" string is not an int, 1 is not a bool), extra fields forbidden, NaN and infinity rejected. JSON true is not accepted as schema_version 1, and synthetic_disclosure must be the JSON boolean true. Nullable fields (marked ? in M0.2) may be omitted and default to null | Implementation choice |
| IC18 | Contract value formats beyond the M0.2 field list: hashes are 64 lowercase hex characters; path fields are relative to the episode folder with forward slashes and no empty, '.', '..', drive, or scheme parts, and the validator never opens a path that resolves outside the folder; a full sources date must exist on the calendar; qa.hard_failures and qa.warnings are at least 0; non-empty means at least one non-space character, and claims.location must be non-empty (D21); contract files are UTF-8 without a byte order mark, strict JSON, with no repeated keys | Implementation choice |
| IC19 | normalize_quote details: curly quotes are U+2018 to U+201F (including low-9 and reversed-9 forms); dashes are hyphen U+2010, non-breaking hyphen U+2011, figure dash U+2012, en dash, em dash, horizontal bar U+2015, and minus sign (D19); soft hyphens (U+00AD) are removed; dashes are mapped and soft hyphens removed before the line-break rule; spaces or tabs around the line break count as part of it; letters are Unicode letters, so a line-break hyphen between digits stays unjoined (D19); line breaks are LF, CRLF, or CR. segment_hash hashes the UTF-8 encoding | Implementation choice |
| IC20 | tft validate on a single file runs SCHEMA_INVALID, DUPLICATE_ID, and every rule that needs only that file; rules that need another file or files on disk run only on a folder (D17). On a folder it first checks EPISODE_FILE_MISSING and UPSTREAM_FILE_MISSING (D20, IC23), then runs the schema rules for each contract file present, then every other rule whose contract files are present and pass their schema. Output is sorted by file in contract order, then rule-table order; the ID column is the entry's ID or -. A file name that is not a contract gives UNKNOWN_CONTRACT and exit 2; tft hash file on a folder gives NOT_A_FILE and exit 2 | Implementation choice |
| IC21 | Rule readings: QUOTE_MISMATCH requires exactly one cited claim, and its quote must match. When another rule already reports the cause (unknown ID or missing file), QUOTE_NOT_FOUND, QUOTE_MISMATCH, SEGMENT_HASH_MISMATCH, and the hash rules skip that entry. A source text that is not valid UTF-8 fails QUOTE_NOT_FOUND. Chapter starts compare as times. ASSET_RIGHTS_UNRESOLVED is reported once per asset, on assets.json. INSUFFICIENT_SOURCES and LONE_CONFLICT_GROUP count distinct IDs. Costs are summed with math.fsum. Rejected claims are skipped by QUOTE_NOT_FOUND, UNKNOWN_SOURCE, and LONE_CONFLICT_GROUP, and REJECTED_CLAIM_CITED fails a segment that cites one (D18) | Implementation choice |
| IC22 | tft schema export writes Pydantic's validation-mode JSON Schema with "$schema" set to draft 2020-12, 2-space indent, UTF-8, LF; --out chooses another folder | Implementation choice |
| IC23 | Upstream map for UPSTREAM_FILE_MISSING, from the stage order in episode.json (sources, claims, script, visuals for scenes.json, assets, package for release.json): sources.json needs none; claims.json needs sources.json; script.json needs sources.json and claims.json; scenes.json needs those and script.json; assets.json needs those and scenes.json; release.json needs all five. episode.json is covered by EPISODE_FILE_MISSING. One problem per present file and missing upstream file. scenes.json may exist before assets.json, so UNKNOWN_ASSET runs only once assets.json exists | Implementation choice |

## Changes

- 2026-11-18, IC5: added that workspace/ is used only when TFT_WORKSPACE is empty. Decided by Steven.
- 2026-11-18, IC8: NFKC removed to match CHARTER.md quote rule. Decided by Steven.
- 2026-11-18, IC20: single-file validate now runs every rule that needs only that file, not just the schema rules (D17). Decided by Steven.
- 2026-11-18, IC21: rejected claims are skipped by QUOTE_NOT_FOUND, UNKNOWN_SOURCE, and LONE_CONFLICT_GROUP; REJECTED_CLAIM_CITED added (D18). Decided by Steven.
- 2026-11-18, IC19: U+2010, U+2011, U+2012, and U+2015 now map to a hyphen; a line-break hyphen between digits stays unjoined (D19). Decided by Steven.
- 2026-11-18, IC20: folder mode now fails without episode.json or when an upstream file is missing, replacing "absent files are not errors" (D20, map in IC23). Decided by Steven.
- 2026-11-18, IC18: claims.location must be non-empty (D21). Decided by Steven.
- 2026-11-18, IC19: added that soft hyphens (U+00AD) are removed, as the M0.2 prompt required. Decided by Steven.
