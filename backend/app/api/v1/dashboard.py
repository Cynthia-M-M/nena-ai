from fastapi import APIRouter, Depends
from app.core.auth import Principal, get_principal, require_membership
from app.schemas.dashboard import FunderDashboardResponse, ClinicDashboardResponse
from app.services.dashboard import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboards & Impact Analytics"])


@router.get("/funder/{organization_id}", response_model=FunderDashboardResponse)
async def get_funder_dashboard(organization_id: str, principal: Principal = Depends(get_principal)):
    """Returns institutional donor dashboard with real-time financial metrics,
    households served, average settlement latency, and regional breakdowns.
    """
    await require_membership(principal, organization_id, ["funder_admin", "funder_analyst", "auditor", "platform_admin"])
    return await dashboard_service.get_funder_dashboard(organization_id)


@router.get("/clinic/{organization_id}", response_model=ClinicDashboardResponse)
async def get_clinic_dashboard(organization_id: str, principal: Principal = Depends(get_principal)):
    """Returns clinic dashboard metrics, settled volume, and pending claims."""
    await require_membership(principal, organization_id, ["clinic_admin", "clinic_staff", "platform_admin"])
    return await dashboard_service.get_clinic_dashboard(organization_id)
