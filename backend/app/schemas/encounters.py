from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class EncounterCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    program_id: UUID
    patient_ref: str = Field(min_length=6, max_length=160, description="Pseudonymous patient voucher reference")
    device_id: UUID
    device_fingerprint: str = Field(min_length=16, max_length=512, description="Client hardware attestation fingerprint")
    treatment_code: Literal["MATERNAL_CARE", "PEDIATRIC_EMERGENCY", "MALARIA_LAB"]
    description: str | None = Field(default=None, max_length=500)
    amount: Decimal = Field(gt=0, le=1_000_000, decimal_places=2)
    currency: Literal["KES", "USD"] = "KES"
    occurred_at: datetime
    idempotency_key: UUID
    offline_created: bool = False


class OTPVerify(BaseModel):
    model_config = ConfigDict(extra="forbid")
    otp: str = Field(pattern=r"^\d{6}$", description="6-digit patient consent OTP")


class EncounterResponse(BaseModel):
    encounter_id: UUID
    status: str
    consent_required: bool
    message: str


class EncounterDetail(BaseModel):
    id: UUID
    clinic_organization_id: UUID
    program_id: UUID
    patient_token_id: UUID
    submitted_by: UUID
    device_id: UUID
    treatment_code: str
    description: str | None = None
    amount: Decimal
    currency: str
    county: str
    occurred_at: datetime
    submitted_at: datetime | None = None
    status: str
    idempotency_key: UUID
    offline_created: bool
    created_at: datetime
