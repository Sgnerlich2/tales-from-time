"""episode.json: where the episode stands, its stages, gates, budget, and error log."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from tft.contracts.common import ContractModel, EpisodeId, SchemaVersion, Stage

EpisodeStatus = Literal["active", "paused_at_gate", "halted_budget", "halted_failure", "done"]
StageStatus = Literal["pending", "running", "done", "failed", "skipped"]
GateState = Literal["pending", "approved", "rejected", "skipped"]
Usd = Annotated[float, Field(ge=0)]


class StageState(ContractModel):
    status: StageStatus
    retries: Annotated[int, Field(ge=0)]
    last_error: str | None = None


class Gate(ContractModel):
    state: GateState
    approver: str | None = None
    decided_at: datetime | None = None


class Gates(ContractModel):
    topic: Gate
    script: Gate
    final: Gate


class CostUsd(ContractModel):
    model: Usd
    voice: Usd
    assets: Usd
    other: Usd


class ErrorLogEntry(ContractModel):
    at: datetime
    stage: Stage
    message: str


class Episode(ContractModel):
    schema_version: SchemaVersion
    episode_id: EpisodeId
    working_title: str
    current_stage: Stage
    status: EpisodeStatus
    stages: dict[Stage, StageState]
    gates: Gates
    budget_cap_usd: float = 10.0
    cost_usd: CostUsd
    error_log: list[ErrorLogEntry]
