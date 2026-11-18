"""Contract model structure, the relative-path rule, and chapter times."""

import re

import pytest
from pydantic import TypeAdapter, ValidationError

from tft.contracts import CONTRACTS
from tft.contracts.common import REL_PATH_PATTERN, RelPath
from tft.contracts.release import chapter_seconds


@pytest.mark.parametrize("name", list(CONTRACTS))
def test_every_top_level_model_has_schema_version_and_episode_id(name):
    fields = CONTRACTS[name].model_fields
    assert {"schema_version", "episode_id"} <= set(fields)


@pytest.mark.parametrize("name", list(CONTRACTS))
def test_every_model_in_a_contract_forbids_extra_fields(name):
    schema = CONTRACTS[name].model_json_schema()
    models = [schema, *schema.get("$defs", {}).values()]
    for model in models:
        if "properties" in model:
            assert model.get("additionalProperties") is False, model.get("title")


@pytest.mark.parametrize(
    ("path", "valid"),
    [
        ("sources/SRC-001.pdf", True),
        ("a.txt", True),
        (".hidden/notes.txt", True),
        ("a/.../b", True),
        ("", False),
        ("/abs/file.txt", False),
        ("C:/file.txt", False),
        ("https://example.invalid/x", False),
        ("sources\\file.txt", False),
        ("a//b", False),
        ("a/./b", False),
        ("a/../b", False),
        ("../outside.txt", False),
        ("folder/", False),
    ],
)
def test_rel_path_check_and_exported_pattern_agree(path, valid):
    try:
        TypeAdapter(RelPath).validate_python(path)
        accepted = True
    except ValidationError:
        accepted = False
    assert accepted is valid
    assert (re.search(REL_PATH_PATTERN, path) is not None) is valid


@pytest.mark.parametrize(
    ("start", "seconds"),
    [("0:00", 0), ("0:45", 45), ("7:30", 450), ("59:59", 3599), ("1:02:03", 3723)],
)
def test_chapter_seconds(start, seconds):
    assert chapter_seconds(start) == seconds
