"""The Problem record and the rule codes the validator reports."""

from dataclasses import dataclass

# The M0.2 rule table, in table order, plus the follow-up codes (D18, D20). Output within
# a file is sorted in this order.
RULE_CODES: tuple[str, ...] = (
    "EPISODE_FILE_MISSING",
    "UPSTREAM_FILE_MISSING",
    "SCHEMA_INVALID",
    "DUPLICATE_ID",
    "RETRY_LIMIT_EXCEEDED",
    "BUDGET_CAP_EXCEEDED",
    "SOURCE_FILE_MISSING",
    "SOURCE_HASH_MISMATCH",
    "INSUFFICIENT_SOURCES",
    "UNKNOWN_SOURCE",
    "QUOTE_NOT_FOUND",
    "LONE_CONFLICT_GROUP",
    "UNKNOWN_CLAIM",
    "REJECTED_CLAIM_CITED",
    "UNCITED_FACTUAL_SEGMENT",
    "QUOTE_MISMATCH",
    "QUOTE_VOICE_MISMATCH",
    "TEXT_HASH_MISMATCH",
    "STALE_VERIFICATION",
    "UNKNOWN_SEGMENT",
    "SEGMENT_HASH_MISMATCH",
    "STATIC_SHOT_TOO_LONG",
    "UNKNOWN_ASSET",
    "ASSET_FILE_MISSING",
    "ASSET_HASH_MISMATCH",
    "ASSET_RIGHTS_UNRESOLVED",
    "UPLOAD_WITHOUT_APPROVAL",
    "CHAPTERS_INVALID",
)


@dataclass(frozen=True)
class Problem:
    """One validation problem, printed as: ERROR <file> <id or -> <CODE> <message>."""

    file: str
    item_id: str
    code: str
    message: str

    def line(self) -> str:
        return f"ERROR {self.file} {self.item_id} {self.code} {self.message}"
