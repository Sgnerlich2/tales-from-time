# Tales From Time

## Project

Tales From Time is a local-first pipeline that turns an approved topic into a publish-ready, source-backed history video of about 8 minutes. Each episode is a folder of versioned JSON files; each stage reads its inputs, validates them, and writes validated outputs.

## Roles

- Steven is the owner and final authority.
- Duet is the chief architect: it writes task prompts and reviews results.
- Claude Code implements and tests.
- The pipeline produces episodes.

## Commands

Run from the repo root in PowerShell.

```powershell
uv sync            # create .venv and install the locked dependencies
uv run pytest      # run the tests
uv run tft --help  # show the CLI and its commands
```

## Layout

```text
tales-from-time/
  CLAUDE.md, README.md, pyproject.toml, uv.lock, .gitignore, .gitattributes, .env.example
  docs/              project records: decisions.md (decision log) and status.md (where work stands)
    style/           style guides for script, voice, and visuals
    experiments/     experiment plans and results
    pilot/           records from the pilot episodes
  schemas/           JSON Schema exported from the Pydantic contracts for the TypeScript side
  scripts/           helper scripts that run from PowerShell; no bash-only scripts
  src/tft/           the tft package; cli.py holds the Typer app behind the tft command
    contracts/       Pydantic v2 contract models (from M0.2)
    validate/        checks behind the validate command (from M0.2)
  tests/             pytest tests
    fixtures/        test fixtures, including the golden fixture of invented, labeled documents
  render/            Remotion project (TypeScript) that renders the finished video; empty for now
  workspace/         git-ignored fallback episode workspace; only .gitkeep is tracked
```

Empty folders hold a .gitkeep file so Git keeps them. Episodes live in TFT_WORKSPACE, outside the repo.

## Platform

- Windows 11 desktop, PowerShell.
- Paths through pathlib.
- Paths inside JSON are relative to the episode folder and use forward slashes.
- Text files are UTF-8 with LF line endings.

## Standing rules

1. Tests use mocked providers. Real API calls only in clearly marked smoke tests with a small spend limit.
2. Never weaken a validator, skip a test, or loosen a threshold to make something pass. Report the failure instead.
3. No new dependency without stating why and what it costs.
4. Contract changes bump the schema version and update the fixtures in the same task.
5. Never commit secrets. Never print or log a key's value. Never set a YouTube video public.
6. Do not install community skills or plugins. Code adapted from a reviewed repository keeps its license notice and is read in full first.
7. Stay inside the task's scope. Note unrelated problems in the report rather than fixing them.
8. Never upload, publish, or change a video's visibility. The pipeline uploads as private at most, and only in M7 or later.

## Records

At the end of every task, update docs/status.md. Record any implementation choice in docs/decisions.md with the label Implementation choice. Do not edit entries labeled Owner confirmed, Recommended, or Assumption; propose changes in the report instead.

## Reporting

End every task with:

- files changed
- tests added
- the actual output of each acceptance command
- open issues
- any deviation and why
