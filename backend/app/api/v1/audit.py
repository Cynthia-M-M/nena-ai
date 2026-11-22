from fastapi import APIRouter, Depends
from app.core.auth import Principal, get_principal, require_membership
from app.core.database import db
from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.schemas.audit import AuditDecision, AuditDetailResponse
from app.repositories.encounter_repository import encounter_repo
from app.services.settlement import settlement_service

router = APIRouter(prefix="/audit", tags=["Governance & Manual Audit"])


@router.get("/encounters")
async def list_flagged_encounters(principal: Principal = Depends(get_principal)):
    """Lists encounters flagged in manual_audit status awaiting human auditor review."""
    return await encounter_repo.list_pending_audits()


@router.get("/encounters/{encounter_id}", response_model=AuditDetailResponse)
async def get_audit_trail(encounter_id: str, principal: Principal = Depends(get_principal)):
    """Retrieves full verification audit trail, anomaly assessments, and ledger evidence."""
    encounter = await encounter_repo.get_encounter(encounter_id)
    if not encounter:
        raise NotFoundError("Encounter not found")

    program = await db.select("funding_programs", {"select": "funder_organization_id", "id": f"eq.{encounter['program_id']}", "limit": "1"})
    try:
        await require_membership(principal, encounter["clinic_organization_id"])
    except ForbiddenError:
        await require_membership(principal, program[0]["funder_organization_id"])

    events = await encounter_repo.get_verification_events(encounter_id)
    risk = await encounter_repo.get_anomaly_assessments(encounter_id)
    ledger = await db.select("ledger_entries", {
        "select": "id,event_type,amount,currency,prev_hash,tx_hash,metadata,created_at",
        "encounter_id": f"eq.{encounter_id}",
        "order": "created_at.asc"
    })
    payouts = []
    if ledger:
        payouts = await db.select("payouts", {
            "select": "id,provider,provider_transaction_id,amount,currency,status,initiated_at,completed_at",
            "ledger_entry_id": f"eq.{ledger[0]['id']}"
        })

    return {
        "encounter": encounter,
        "verification_events": events,
        "risk_assessments": risk,
        "ledger": ledger,
        "payouts": payouts
    }


@router.post("/encounters/{encounter_id}/decision")
async def review_flagged_encounter(encounter_id: str, payload: AuditDecision, principal: Principal = Depends(get_principal)):
    """Submits human auditor decision for an encounter in manual_audit.
    Approved encounters proceed to atomic ledger authorization and payout.
    Rejected encounters are finalized and cannot be paid.
    """
    encounter = await encounter_repo.get_encounter(encounter_id)
    if not encounter:
        raise NotFoundError("Encounter not found")

    program = await db.select("funding_programs", {"select": "funder_organization_id", "id": f"eq.{encounter['program_id']}", "limit": "1"})
    await require_membership(principal, program[0]["funder_organization_id"], ["funder_admin", "auditor", "platform_admin"])

    if encounter["status"] != "manual_audit":
        raise ConflictError(f"Only encounters in manual_audit status can be reviewed (current status: {encounter['status']})")

    if payload.decision == "reject":
        await encounter_repo.update({"id": f"eq.{encounter_id}"}, {"status": "rejected"})
        await encounter_repo.record_verification_event(
            encounter_id=encounter_id,
            stage="anomaly_detection",
            status="failed",
            reason_code="HUMAN_AUDITOR_REJECTED",
            details={"decision": "reject", "reason": payload.reason, "auditor_id": principal.user_id},
            verified_by=principal.user_id
        )
        return {"encounter_id": encounter_id, "status": "rejected", "message": f"Auditor rejected claim: {payload.reason}"}

    # If approved by human auditor:
    await encounter_repo.record_anomaly_assessment(encounter_id, {
        "risk_score": 0,
        "risk_level": "low",
        "flags": [{"code": "HUMAN_AUDIT_OVERRIDE", "reason": payload.reason}],
        "recommended_action": "approve"
    })
    await encounter_repo.record_verification_event(
        encounter_id=encounter_id,
        stage="anomaly_detection",
        status="passed",
        reason_code="HUMAN_AUDITOR_APPROVED",
        details={"decision": "approve", "reason": payload.reason, "auditor_id": principal.user_id},
        verified_by=principal.user_id
    )
    await encounter_repo.update({"id": f"eq.{encounter_id}"}, {"status": "pending_verification"})

    return await settlement_service.authorize_and_settle(encounter_id)
