"""scenes.json: the visual plan, each scene tied to a script segment and its assets."""

from typing import Annotated, Any, Literal

from pydantic import Field, ValidationInfo, field_validator

from tft.contracts.common import AssetId, ContractModel, EpisodeId, SceneId, SchemaVersion, SegmentId, Sha256Hex


class Scene(ContractModel):
    scene_id: SceneId
    segment_id: SegmentId
    segment_hash: Sha256Hex
    component: Literal["map_zoom", "document_quote", "archival_pan", "chapter_card", "timeline"]
    props: dict[str, Any]
    asset_ids: list[AssetId]
    citation: str | None = Field(default=None, validate_default=True)
    motion: Literal["static", "animated"]
    start_s: Annotated[float, Field(ge=0)]
    duration_s: Annotated[float, Field(gt=0)]

    @field_validator("citation")
    @classmethod
    def _citation_required_for_document_quote(cls, value: str | None, info: ValidationInfo) -> str | None:
        if info.data.get("component") == "document_quote" and (value is None or not value.strip()):
            raise ValueError("citation is required when component is document_quote")
        return value


class Scenes(ContractModel):
    schema_version: SchemaVersion
    episode_id: EpisodeId
    scenes: list[Scene]
