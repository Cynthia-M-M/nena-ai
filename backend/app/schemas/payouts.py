from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class PayoutResponse(BaseModel):
    id: UUID
    ledger_entry_id: UUID
    provider: str
    provider_transaction_id: str | None = None
    amount: Decimal
    currency: str
    status: str
    initiated_at: datetime
    completed_at: datetime | None = None


class PayoutSimulateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["completed", "failed"]
    result_code: str = "0"
    result_desc: str = "Simulated manual provider callback"
