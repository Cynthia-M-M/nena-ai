from datetime import datetime, timezone
from app.core.database import db
from app.core.errors import ConflictError, NotFoundError
from app.repositories.encounter_repository import encounter_repo
from app.repositories.ledger_repository import ledger_repo
from app.integrations.mpesa_mock import mpesa
from app.core.logging import safe_logger


class SettlementService:
    """Orchestrates atomic financial authorization and simulated M-Pesa Daraja settlement."""

    async def authorize_and_settle(self, encounter_id: str) -> dict:
        encounter = await encounter_repo.get_encounter(encounter_id)
        if not encounter:
            raise NotFoundError("Encounter not found")

        # 1. Enforce that all 4 verification stages passed
        events = await encounter_repo.get_verification_events(encounter_id)
        passed_stages = {x["stage"] for x in events if x["status"] == "passed"}
        required_stages = {"identity_device", "patient_consent", "program_policy", "anomaly_detection"}
        if not required_stages.issubset(passed_stages):
            missing = required_stages - passed_stages
            raise ConflictError(f"All 4 verification stages must pass before authorization (missing: {missing})")

        # 2. Execute database-level atomic authorization & row lock
        auth_result = await ledger_repo.authorize_encounter(encounter_id)
        payout_info = auth_result[0] if isinstance(auth_result, list) else auth_result
        if not payout_info:
            raise ConflictError("Database authorization returned no valid payout structure")

        payout_id = payout_info["payout_id"]
        amount_str = str(encounter["amount"])
        currency_str = encounter["currency"]

        # 3. Dispatch simulated M-Pesa B2C Payout
        phone_synthetic = "254700000001"
        provider_resp = await mpesa.disburse(
            phone=phone_synthetic,
            amount=amount_str,
            currency=currency_str,
            reference=encounter_id
        )

        now = datetime.now(timezone.utc).isoformat()

        if provider_resp.get("success"):
            # Provider confirmed payment: advance payout and encounter to settled
            await db.patch("payouts", {"id": f"eq.{payout_id}"}, {
                "status": "completed",
                "provider_transaction_id": provider_resp["transaction_id"],
                "provider_response": provider_resp,
                "completed_at": now
            })
            await db.patch("care_encounters", {"id": f"eq.{encounter_id}"}, {
                "status": "settled"
            })
            safe_logger.info(f"Encounter {encounter_id} successfully settled via simulated Daraja {provider_resp['transaction_id']}")
            return {
                "encounter_id": encounter_id,
                "status": "settled",
                "payout_id": payout_id,
                "provider": "MPESA_MOCK",
                "provider_transaction_id": provider_resp["transaction_id"],
                "amount": amount_str,
                "currency": currency_str,
                "settlement_mode": "SIMULATED_NOT_REAL_MONEY"
            }
        else:
            # Payment failed at provider: NEVER report as settled
            await db.patch("payouts", {"id": f"eq.{payout_id}"}, {
                "status": "failed",
                "provider_response": provider_resp
            })
            await db.patch("care_encounters", {"id": f"eq.{encounter_id}"}, {
                "status": "settlement_pending"
            })
            safe_logger.warning(f"Daraja payout failed for encounter {encounter_id}: {provider_resp.get('result_desc')}")
            return {
                "encounter_id": encounter_id,
                "status": "settlement_pending",
                "payout_id": payout_id,
                "provider": "MPESA_MOCK",
                "message": "Settlement rejected by provider; authorization reserved for reconciliation"
            }


settlement_service = SettlementService()
