"""The committed JSON Schema files must equal a fresh export."""

from pathlib import Path

from tft.contracts import json_schemas

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"


def test_committed_schema_files_match_a_fresh_export():
    expected = json_schemas()
    assert sorted(path.name for path in SCHEMAS.glob("*.schema.json")) == sorted(expected)
    for name, text in expected.items():
        assert (SCHEMAS / name).read_bytes() == text.encode("utf-8"), f"{name} is stale: run uv run tft schema export"
