"""Pydantic v2 models for the seven episode contract files, and their JSON Schema export."""

import json

from pydantic import BaseModel

from tft.contracts.assets import Assets
from tft.contracts.claims import Claims
from tft.contracts.episode import Episode
from tft.contracts.release import Release
from tft.contracts.scenes import Scenes
from tft.contracts.script import Script
from tft.contracts.sources import Sources

# Contract name to model, in validation order. Each contract lives in <name>.json.
CONTRACTS: dict[str, type[BaseModel]] = {
    "episode": Episode,
    "sources": Sources,
    "claims": Claims,
    "script": Script,
    "scenes": Scenes,
    "assets": Assets,
    "release": Release,
}

# Contract file name to contract name, for example "claims.json" to "claims".
CONTRACT_FILES: dict[str, str] = {f"{name}.json": name for name in CONTRACTS}

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"


def json_schemas() -> dict[str, str]:
    """Return {file name: JSON text} for every contract's JSON Schema, as `tft schema export` writes them."""
    rendered: dict[str, str] = {}
    for name, model in CONTRACTS.items():
        schema = {"$schema": JSON_SCHEMA_DIALECT, **model.model_json_schema()}
        rendered[f"{name}.schema.json"] = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
    return rendered


__all__ = [
    "CONTRACTS",
    "CONTRACT_FILES",
    "Assets",
    "Claims",
    "Episode",
    "Release",
    "Scenes",
    "Script",
    "Sources",
    "json_schemas",
]
