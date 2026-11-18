"""release.json: the finished video's checks, metadata, approval, and upload state."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from tft.contracts.common import ContractModel, EpisodeId, RelPath, SchemaVersion, Sha256Hex, TrueFlag

# m:ss (minutes 0 to 59) or h:mm:ss.
CHAPTER_TIME_PATTERN = r"^(?:[0-5]?[0-9]:[0-5][0-9]|[0-9]+:[0-5][0-9]:[0-5][0-9])$"
ChapterTime = Annotated[str, StringConstraints(pattern=CHAPTER_TIME_PATTERN)]


def chapter_seconds(start: str) -> int:
    """Seconds from the start of the video for a chapter time in m:ss or h:mm:ss form."""
    seconds = 0
    for part in start.split(":"):
        seconds = seconds * 60 + int(part)
    return seconds


class QaSummary(ContractModel):
    hard_failures: Annotated[int, Field(ge=0)]
    warnings: Annotated[int, Field(ge=0)]
    report_path: RelPath


class Chapter(ContractModel):
    start: ChapterTime
    title: str


class Release(ContractModel):
    schema_version: SchemaVersion
    episode_id: EpisodeId
    video_sha256: Sha256Hex | None = None
    loudness_lufs: float | None = None
    true_peak_dbtp: float | None = None
    qa: QaSummary | None = None
    title: str
    description: str
    chapters: list[Chapter]
    captions_sha256: Sha256Hex | None = None
    synthetic_disclosure: TrueFlag
    visibility: Literal["private"]
    approver: str | None = None
    approved_at: datetime | None = None
    youtube_id: str | None = None
