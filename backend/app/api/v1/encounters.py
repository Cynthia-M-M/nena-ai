from fastapi import APIRouter, Depends
from app.core.auth import Principal, get_principal, require_membership
from app.core.database import db
from app.core.errors import ForbiddenError, NotFoundError
from app.schemas.encounters import EncounterCreate, OTPVerify, EncounterResponse, EncounterDetail
from app.services.verification import verification_service
from app.services.settlement import settlement_service

router = APIRouter(prefix="/encounters", tags=["Care Encounters"])


@router.post("", status_code=201, response_model=EncounterResponse)
async def submit_encounter(payload: EncounterCreate, principal: Principal = Depends(get_principal)):
    """Submits a clinical encounter for subsidy authorization. Clinic identity is derived
    from the authenticated user's active membership, preventing clinic spoofing.
    """
    memberships = await db.select("org_memberships", {
        "select": "organization_id,role",
        "user_id": f"eq.{principal.user_id}",
        "active": "eq.true",
        "role": "in.(clinic_admin,clinic_staff)",
        "limit": "10"
    })

    if not memberships:
        raise ForbiddenError("User must have an active clinic staff or clinic admin membership")

    clinic_id = memberships[0]["organization_id"]
    return await verification_service.submit_encounter(payload.model_dump(mode="json"), principal, clinic_id)


@router.post("/{encounter_id}/consent")
async def confirm_patient_consent(encounter_id: str, payload: OTPVerify, principal: Principal = Depends(get_principal)):
    """Validates patient consent OTP and completes Stages 2, 3, 4 of Zero-Trust verification.
    Approved claims automatically trigger atomic ledger authorization and simulated settlement.
    """
    memberships = await db.select("org_memberships", {
        "select": "organization_id",
        "user_id": f"eq.{principal.user_id}",
        "active": "eq.true",
        "role": "in.(clinic_admin,clinic_staff)",
        "limit": "10"
    })
    if not memberships:
        raise ForbiddenError("Active clinic membership required to verify consent")

    clinic_id = memberships[0]["organization_id"]
    eval_result = await verification_service.verify_consent_and_evaluate(encounter_id, payload.otp, principal, clinic_id)

    if eval_result.get("status") == "approved_for_authorization":
        return await settlement_service.authorize_and_settle(encounter_id)

    return eval_result


@router.get("/{encounter_id}", response_model=EncounterDetail)
async def get_encounter(encounter_id: str, principal: Principal = Depends(get_principal)):
    """Retrieves care encounter details with tenant access verification."""
    rows = await db.select("care_encounters", {"select": "*", "id": f"eq.{encounter_id}", "limit": "1"})
    if not rows:
        raise NotFoundError("Encounter not found")
    encounter = rows[0]

    # Verify membership in either clinic or funding organization
    try:
        await require_membership(principal, encounter["clinic_organization_id"])
    except ForbiddenError:
        program = await db.select("funding_programs", {"select": "funder_organization_id", "id": f"eq.{encounter['program_id']}", "limit": "1"})
        if not program:
            raise NotFoundError("Encounter program not found")
        await require_membership(principal, program[0]["funder_organization_id"])

    return encounter
