from app.repositories.base import BaseRepository
from app.core.security import keyed_hash


class ProgramRepository(BaseRepository):
    def __init__(self):
        super().__init__("funding_programs")

    async def get_active_rules(self, program_id: str) -> dict | None:
        rows = await self.db.select("program_rules", {
            "select": "*",
            "program_id": f"eq.{program_id}",
            "active": "eq.true",
            "order": "version.desc",
            "limit": "1"
        })
        return rows[0] if rows else None

    async def get_clinic_enrollment(self, program_id: str, clinic_org_id: str) -> dict | None:
        rows = await self.db.select("clinic_enrollments", {
            "select": "*",
            "program_id": f"eq.{program_id}",
            "clinic_organization_id": f"eq.{clinic_org_id}",
            "active": "eq.true",
            "limit": "1"
        })
        return rows[0] if rows else None

    async def get_patient_token(self, program_id: str, raw_patient_ref: str) -> dict | None:
        ref_hash = keyed_hash(raw_patient_ref, "patient-reference")
        rows = await self.db.select("patient_tokens", {
            "select": "*",
            "program_id": f"eq.{program_id}",
            "patient_ref_hash": f"eq.{ref_hash}",
            "limit": "1"
        })
        return rows[0] if rows else None


program_repo = ProgramRepository()
