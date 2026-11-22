from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ProgramRuleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_amount_per_visit: Decimal = Field(gt=0, le=1_000_000)
    approved_treatment_codes: list[str] = Field(min_length=1, max_length=30)
    allowed_counties: list[str] = Field(min_length=1, max_length=47)
    requires_patient_otp: bool = True
    max_daily_claims: int = Field(default=100, ge=1, le=10000)
    max_household_claims_per_day: int = Field(default=3, ge=1, le=100)


class ProgramRuleResponse(BaseModel):
    id: UUID
    program_id: UUID
    max_amount_per_visit: Decimal
    approved_treatment_codes: list[str]
    allowed_counties: list[str]
    requires_patient_otp: bool
    max_daily_claims: int
    max_household_claims_per_day: int
    active: bool
    version: int
    created_at: datetime


class FundingProgramResponse(BaseModel):
    id: UUID
    funder_organization_id: UUID
    program_name: str
    description: str | None = None
    currency: str
    allocated_amount: Decimal
    starts_at: datetime
    ends_at: datetime | None = None
    active: bool
    created_at: datetime
    active_rules: ProgramRuleResponse | None = None
