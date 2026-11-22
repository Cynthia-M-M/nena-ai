from datetime import datetime, timezone
from app.repositories.base import BaseRepository


class EncounterRepository(BaseRepository):
    def __init__(self):
        super().__init__("care_encounters")

    async def get_encounter(self, encounter_id: str) -> dict | None:
        rows = await self.db.select("care_encounters", {
            "select": "*",
            "id": f"eq.{encounter_id}",
            "limit": "1"
        })
        return rows[0] if rows else None

    async def get_consent_challenge(self, encounter_id: str) -> dict | None:
        rows = await self.db.select("consent_challenges", {
            "select": "*",
            "encounter_id": f"eq.{encounter_id}",
            "limit": "1"
        })
        return rows[0] if rows else None

    async def create_consent_challenge(self, encounter_id: str, otp_hash: str, expires_at: datetime) -> dict:
        payload = {
            "encounter_id": encounter_id,
            "otp_hash": otp_hash,
            "expires_at": expires_at.isoformat(),
            "attempts": 0
        }
        rows = await self.db.insert("consent_challenges", payload)
        return rows[0]

    async def record_verification_event(self, encounter_id: str, stage: str, status: str, reason_code: str, details: dict | None = None, verified_by: str = "nena-zero-trust"):
        await self.db.insert("verification_events", {
            "encounter_id": encounter_id,
            "stage": stage,
            "status": status,
            "reason_code": reason_code,
            "details": details or {},
            "verified_by": verified_by
        })

    async def get_verification_events(self, encounter_id: str) -> list[dict]:
        return await self.db.select("verification_events", {
            "select": "*",
            "encounter_id": f"eq.{encounter_id}",
            "order": "created_at.asc"
        })

    async def record_anomaly_assessment(self, encounter_id: str, risk: dict) -> dict:
        payload = {
            "encounter_id": encounter_id,
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "flags": risk["flags"],
            "recommended_action": risk["recommended_action"]
        }
        rows = await self.db.insert("anomaly_assessments", payload)
        return rows[0]

    async def get_anomaly_assessments(self, encounter_id: str) -> list[dict]:
        return await self.db.select("anomaly_assessments", {
            "select": "*",
            "encounter_id": f"eq.{encounter_id}",
            "order": "created_at.desc"
        })

    async def get_recent_claims(self, program_id: str, exclude_id: str | None = None, limit: int = 100) -> list[dict]:
        params = {
            "select": "id,patient_token_id,treatment_code,clinic_organization_id,amount,occurred_at,submitted_at",
            "program_id": f"eq.{program_id}",
            "order": "submitted_at.desc",
            "limit": str(limit)
        }
        if exclude_id:
            params["id"] = f"neq.{exclude_id}"
        return await self.db.select("care_encounters", params)

    async def list_pending_audits(self, funder_org_id: str | None = None) -> list[dict]:
        # Filter encounters with status 'manual_audit'
        params = {"select": "*", "status": "eq.manual_audit", "order": "submitted_at.desc"}
        return await self.db.select("care_encounters", params)


encounter_repo = EncounterRepository()
