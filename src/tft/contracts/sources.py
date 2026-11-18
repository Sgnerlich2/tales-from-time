"""sources.json: each saved source with its files, hashes, tier, and bias note."""

import datetime as dt
from typing import Annotated, Literal

from pydantic import AfterValidator, StringConstraints

from tft.contracts.common import (
    ContractModel,
    EpisodeId,
    NonEmptyStr,
    RelPath,
    SchemaVersion,
    Sha256Hex,
    SourceId,
)

# YYYY, YYYY-MM, or YYYY-MM-DD.
SOURCE_DATE_PATTERN = r"^[0-9]{4}(?:-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|[12][0-9]|3[01]))?)?$"


def _check_calendar_date(value: str) -> str:
    # The pattern allows 1901-02-30; a full date must also exist on the calendar.
    if len(value) == 10:
        dt.date.fromisoformat(value)
    return value


SourceDate = Annotated[str, StringConstraints(pattern=SOURCE_DATE_PATTERN), AfterValidator(_check_calendar_date)]


class Source(ContractModel):
    source_id: SourceId
    title: str
    author: str
    date: SourceDate
    tier: Literal["primary", "scholarly"]
    url: str
    local_path: RelPath
    sha256: Sha256Hex
    text_path: RelPath
    text_sha256: Sha256Hex
    retrieved: dt.date
    bias_note: NonEmptyStr


class Sources(ContractModel):
    schema_version: SchemaVersion
    episode_id: EpisodeId
    sources: list[Source]
