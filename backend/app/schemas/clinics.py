from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ClinicProfileResponse(BaseModel):
    organization_id: UUID
    facility_code: str
    county: str
    sub_county: str | None = None
    physical_address: str | None = None
    verification_status: str
    created_at: datetime


class DeviceRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    device_name: str = Field(min_length=3, max_length=100)
    device_fingerprint: str = Field(min_length=16, max_length=512)


class DeviceResponse(BaseModel):
    id: UUID
    clinic_organization_id: UUID
    device_name: str
    active: bool
    registered_at: datetime | None = None
    last_seen_at: datetime | None = None
