"""claims.json: claims extracted from sources, each carrying a verbatim quote."""

from typing import Literal

from tft.contracts.common import (
    ClaimId,
    ConflictGroupId,
    ContractModel,
    EpisodeId,
    NonEmptyStr,
    SchemaVersion,
    SourceId,
)


class Claim(ContractModel):
    claim_id: ClaimId
    text: str
    source_id: SourceId
    location: NonEmptyStr  # CHARTER.md: every claim carries its page or location
    quote: NonEmptyStr
    evidence_strength: Literal["strong", "moderate", "weak"]
    conflict_group: ConflictGroupId | None = None
    status: Literal["extracted", "verified", "rejected"]


class Claims(ContractModel):
    schema_version: SchemaVersion
    episode_id: EpisodeId
    claims: list[Claim]
