"""assets.json: every visual and audio asset with its file, hash, origin, and rights."""

from typing import Literal

from tft.contracts.common import AssetId, ContractModel, EpisodeId, RelPath, SchemaVersion, Sha256Hex


class Asset(ContractModel):
    asset_id: AssetId
    path: RelPath
    sha256: Sha256Hex
    kind: Literal["image", "map_data", "audio", "music", "font", "other"]
    source_url: str
    creator: str
    archive: str
    date: str
    original_status: Literal["public_domain", "cc0", "cc_by", "cc_by_sa", "licensed", "unknown"]
    reproduction_license: str
    attribution: str
    rights_status: Literal["cleared", "unresolved", "missing"]


class Assets(ContractModel):
    schema_version: SchemaVersion
    episode_id: EpisodeId
    assets: list[Asset]
