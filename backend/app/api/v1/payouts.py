from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header
from app.core.auth import Principal, get_principal, require_membership
from app.core.database import db
from app.core.errors import NotFoundError, ForbiddenError
from app.schemas.payouts import PayoutSimulateRequest, PayoutResponse
from app.integrations.mpesa_mock import mpesa

router = APIRouter(prefix="/payouts", tags=["Settlement & Simulated Payouts"])


@router.post("/{payout_id}/simulate")
async def simulate_payout_callback(
    payout_id: str,
    payload: PayoutSimulateRequest,
    principal: Principal = Depends(get_principal),
    x_mpesa_signature: str | None = Header(default=None)
):
    """Simulates an M-Pesa provider callback or retry handling.
    Allows manual testing of provider success, failure, and settlement reconciliation.
    """
    rows = await db.select("payouts", {"select": "*", "id": f"eq.{payout_id}", "limit": "1"})
    if not rows:
        raise NotFoundError("Payout not found")
    payout = rows[0]

    now = datetime.now(timezone.utc).isoformat()
    if payload.status == "completed":
        tx_id = f"NENA_SIM_{payout_id[:8].upper()}"
        await db.patch("payouts", {"id": f"eq.{payout_id}"}, {
            "status": "completed",
            "provider_transaction_id": tx_id,
            "provider_response": {"simulated": True, "code": payload.result_code, "desc": payload.result_desc},
            "completed_at": now
        })
        # Advance encounter to settled
        ledger = await db.select("ledger_entries", {"select": "encounter_id", "id": f"eq.{payout['ledger_entry_id']}", "limit": "1"})
        if ledger:
            await db.patch("care_encounters", {"id": f"eq.{ledger[0]['encounter_id']}"}, {"status": "settled"})
        return {"payout_id": payout_id, "status": "completed", "transaction_id": tx_id}
    else:
        await db.patch("payouts", {"id": f"eq.{payout_id}"}, {
            "status": "failed",
            "provider_response": {"simulated": True, "code": payload.result_code, "desc": payload.result_desc}
        })
        ledger = await db.select("ledger_entries", {"select": "encounter_id", "id": f"eq.{payout['ledger_entry_id']}", "limit": "1"})
        if ledger:
            await db.patch("care_encounters", {"id": f"eq.{ledger[0]['encounter_id']}"}, {"status": "settlement_pending"})
        return {"payout_id": payout_id, "status": "failed", "desc": payload.result_desc}
