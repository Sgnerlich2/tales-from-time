"""script.json: the script as segments, each tied to the claims it cites."""

from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from tft.contracts.common import ClaimId, ContractModel, EpisodeId, SchemaVersion, SegmentId, Sha256Hex

TitleOption = Annotated[str, StringConstraints(max_length=100)]


class Segment(ContractModel):
    segment_id: SegmentId
    act: Annotated[int, Field(ge=1, le=5)]
    text: str
    claim_ids: list[ClaimId]
    is_factual: bool
    is_quote: bool
    voice: Literal["narrator", "quote"]
    text_hash: Sha256Hex
    verified_hash: Sha256Hex | None = None
    verification_status: Literal["unverified", "passed", "failed", "flagged"]


class Script(ContractModel):
    schema_version: SchemaVersion
    episode_id: EpisodeId
    angle: str
    title_options: Annotated[list[TitleOption], Field(min_length=1, max_length=5)]
    target_words: Annotated[int, Field(gt=0)]
    segments: list[Segment]
