from decimal import Decimal
from typing import Any
from uuid import UUID
from pydantic import BaseModel


class RegionalMetric(BaseModel):
    encounters: int
    amount: Decimal


class ProgramSummary(BaseModel):
    program_id: UUID
    program_name: str
    currency: str
    allocated: Decimal
    authorized: Decimal
    remaining: Decimal


class FunderDashboardResponse(BaseModel):
    funder_organization_id: UUID
    total_encounters: int
    households_served: int
    total_allocated: Decimal
    total_authorized: Decimal
    total_settled: Decimal
    remaining_capital: Decimal
    average_settlement_latency_ms: int
    regional_breakdown: dict[str, RegionalMetric]
    suspicious_claims_count: int
    programs: list[ProgramSummary]


class ClinicDashboardResponse(BaseModel):
    clinic_organization_id: UUID
    clinic_name: str
    county: str
    verification_status: str
    total_encounters: int
    total_settled_amount: Decimal
    pending_verification_count: int
    recent_encounters: list[dict[str, Any]]
