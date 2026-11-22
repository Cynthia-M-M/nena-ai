from fastapi import APIRouter, Depends
from app.core.auth import Principal, get_principal, require_membership
from app.core.database import db
from app.core.errors import NotFoundError
from app.schemas.clinics import ClinicProfileResponse, DeviceRegisterRequest, DeviceResponse
from app.repositories.clinic_repository import clinic_repo

router = APIRouter(prefix="/clinics", tags=["Clinic & Device Management"])


@router.get("/{organization_id}", response_model=ClinicProfileResponse)
async def get_clinic(organization_id: str, principal: Principal = Depends(get_principal)):
    """Retrieves clinic profile information."""
    profile = await clinic_repo.get_profile(organization_id)
    if not profile:
        raise NotFoundError("Clinic profile not found")
    return profile


@router.get("/{organization_id}/devices", response_model=list[DeviceResponse])
async def list_devices(organization_id: str, principal: Principal = Depends(get_principal)):
    """Lists registered devices for a clinic facility."""
    await require_membership(principal, organization_id)
    return await clinic_repo.list_devices(organization_id)


@router.post("/{organization_id}/devices", response_model=DeviceResponse)
async def register_device(organization_id: str, payload: DeviceRegisterRequest, principal: Principal = Depends(get_principal)):
    """Registers a clinic hardware tablet or terminal."""
    await require_membership(principal, organization_id, ["clinic_admin", "platform_admin"])
    return await clinic_repo.register_device(organization_id, payload.device_name, payload.device_fingerprint)


@router.delete("/{organization_id}/devices/{device_id}")
async def revoke_device(organization_id: str, device_id: str, principal: Principal = Depends(get_principal)):
    """Revokes a registered clinic device, preventing further claim submissions."""
    await require_membership(principal, organization_id, ["clinic_admin", "platform_admin"])
    success = await clinic_repo.revoke_device(device_id, organization_id)
    if not success:
        raise NotFoundError("Device not found or already inactive")
    return {"device_id": device_id, "revoked": True}
