# Tales From Time

Tales From Time is a local-first pipeline that turns an approved topic into a publish-ready, source-backed history video of about 8 minutes. Each episode is a folder of versioned JSON files kept outside this repo; each pipeline stage reads its inputs, validates them, and writes validated outputs.

## Setup

Install [uv](https://docs.astral.sh/uv/), then run this from the repo root in PowerShell. It creates `.venv` with Python 3.12 and the locked dependencies; uv downloads Python 3.12 if it is missing.

```powershell
uv sync
```

## Tests

```powershell
uv run pytest
```

## Working on the project

Rules, commands, layout, and record keeping are in [CLAUDE.md](CLAUDE.md). Read it before starting a task.
