from typing import Literal, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AuditDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "reject"]
    reason: str = Field(min_length=10, max_length=1000, description="Documented auditor rationale")


class VerificationEventResponse(BaseModel):
    id: UUID
    encounter_id: UUID
    stage: str
    status: str
    reason_code: str | None = None
    details: dict[str, Any] = {}
    verified_by: str


class AuditDetailResponse(BaseModel):
    encounter: dict[str, Any]
    verification_events: list[dict[str, Any]]
    risk_assessments: list[dict[str, Any]]
    ledger: list[dict[str, Any]]
    payouts: list[dict[str, Any]]
