from app.repositories.base import BaseRepository
from app.core.security import keyed_hash, constant_time_equal


class ClinicRepository(BaseRepository):
    def __init__(self):
        super().__init__("clinic_profiles")

    async def get_profile(self, organization_id: str) -> dict | None:
        rows = await self.db.select("clinic_profiles", {
            "select": "*",
            "organization_id": f"eq.{organization_id}",
            "limit": "1"
        })
        return rows[0] if rows else None

    async def get_device(self, device_id: str, clinic_org_id: str) -> dict | None:
        rows = await self.db.select("registered_devices", {
            "select": "*",
            "id": f"eq.{device_id}",
            "clinic_organization_id": f"eq.{clinic_org_id}",
            "limit": "1"
        })
        return rows[0] if rows else None

    async def list_devices(self, clinic_org_id: str) -> list[dict]:
        return await self.db.select("registered_devices", {
            "select": "*",
            "clinic_organization_id": f"eq.{clinic_org_id}",
            "order": "registered_at.desc"
        })

    async def register_device(self, clinic_org_id: str, device_name: str, raw_fingerprint: str) -> dict:
        from datetime import datetime, timezone
        fp_hash = keyed_hash(raw_fingerprint, "device-fingerprint")
        payload = {
            "clinic_organization_id": clinic_org_id,
            "device_name": device_name,
            "device_fingerprint_hash": fp_hash,
            "active": True,
            "registered_at": datetime.now(timezone.utc).isoformat()
        }
        rows = await self.db.insert("registered_devices", payload)
        return rows[0]

    async def revoke_device(self, device_id: str, clinic_org_id: str) -> bool:
        rows = await self.db.patch("registered_devices", {
            "id": f"eq.{device_id}",
            "clinic_organization_id": f"eq.{clinic_org_id}"
        }, {"active": False})
        return len(rows) > 0


clinic_repo = ClinicRepository()
