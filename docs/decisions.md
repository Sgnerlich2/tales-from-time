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
| IC18 | Contract value formats beyond the M0.2 field list: hashes are 64 lowercase hex characters; path fields are relative to the episode folder with forward slashes and no empty, '.', '..', drive, or scheme parts, and the validator never opens a path that resolves outside the folder; a full sources date must exist on the calendar; qa.hard_failures and qa.warnings are at least 0; non-empty means at least one non-space character; contract files are UTF-8 without a byte order mark, strict JSON, with no repeated keys | Implementation choice |
| IC19 | normalize_quote details: curly quotes are U+2018 to U+201F (including low-9 and reversed-9 forms); dashes are en dash, em dash, and minus sign only; dashes are mapped before the line-break rule; spaces or tabs around the line break count as part of it; letters are Unicode letters; line breaks are LF, CRLF, or CR. segment_hash hashes the UTF-8 encoding | Implementation choice |
| IC20 | tft validate on a single file runs the schema rules only (SCHEMA_INVALID and DUPLICATE_ID). On a folder it runs those for each contract file present, then every other rule whose contract files are present and pass their schema; absent files are not errors. Output is sorted by file in contract order, then rule-table order; the ID column is the entry's ID or -. A file name that is not a contract gives UNKNOWN_CONTRACT and exit 2; tft hash file on a folder gives NOT_A_FILE and exit 2 | Implementation choice |
| IC21 | Rule readings: QUOTE_MISMATCH requires exactly one cited claim, and its quote must match. When another rule already reports the cause (unknown ID or missing file), QUOTE_NOT_FOUND, QUOTE_MISMATCH, SEGMENT_HASH_MISMATCH, and the hash rules skip that entry. A source text that is not valid UTF-8 fails QUOTE_NOT_FOUND. Chapter starts compare as times. ASSET_RIGHTS_UNRESOLVED is reported once per asset, on assets.json. INSUFFICIENT_SOURCES and LONE_CONFLICT_GROUP count distinct IDs. Costs are summed with math.fsum | Implementation choice |
| IC22 | tft schema export writes Pydantic's validation-mode JSON Schema with "$schema" set to draft 2020-12, 2-space indent, UTF-8, LF; --out chooses another folder | Implementation choice |

## Changes

- 2026-11-18, IC5: added that workspace/ is used only when TFT_WORKSPACE is empty. Decided by Steven.
- 2026-11-18, IC8: NFKC removed to match CHARTER.md quote rule. Decided by Steven.
