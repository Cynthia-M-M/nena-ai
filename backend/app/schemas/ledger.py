from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class LedgerEntryResponse(BaseModel):
    id: UUID
    encounter_id: UUID
    program_id: UUID
    clinic_organization_id: UUID
    funder_organization_id: UUID
    event_type: str
    amount: Decimal
    currency: str
    prev_hash: str
    tx_hash: str
    metadata: dict[str, Any] = {}
    created_by: UUID | None = None
    created_at: datetime


class LedgerChainVerifyResponse(BaseModel):
    verified: bool
    total_entries: int
    current_head_hash: str
    inconsistencies: list[dict[str, Any]] = []


class LedgerReversalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=10, max_length=1000)
