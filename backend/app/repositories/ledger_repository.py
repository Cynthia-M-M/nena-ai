from app.repositories.base import BaseRepository


class LedgerRepository(BaseRepository):
    def __init__(self):
        super().__init__("ledger_entries")

    async def get_entries_for_encounter(self, encounter_id: str) -> list[dict]:
        return await self.db.select("ledger_entries", {
            "select": "id,encounter_id,program_id,clinic_organization_id,funder_organization_id,event_type,amount,currency,prev_hash,tx_hash,metadata,created_by,created_at",
            "encounter_id": f"eq.{encounter_id}",
            "order": "created_at.asc"
        })

    async def get_entries_for_program(self, program_id: str) -> list[dict]:
        return await self.db.select("ledger_entries", {
            "select": "id,encounter_id,event_type,amount,currency,tx_hash,created_at",
            "program_id": f"eq.{program_id}",
            "order": "created_at.desc"
        })

    async def authorize_encounter(self, encounter_id: str) -> dict:
        return await self.db.rpc("authorize_encounter", {"p_encounter_id": encounter_id})

    async def verify_chain(self) -> dict:
        return await self.db.rpc("verify_ledger_chain", {})

    async def reverse_entry(self, ledger_id: str, reason: str, actor_id: str) -> dict:
        return await self.db.rpc("reverse_ledger_entry", {
            "p_ledger_id": ledger_id,
            "p_reason": reason,
            "p_actor_id": actor_id
        })

    async def get_payout_for_ledger(self, ledger_entry_id: str) -> dict | None:
        rows = await self.db.select("payouts", {
            "select": "*",
            "ledger_entry_id": f"eq.{ledger_entry_id}",
            "limit": "1"
        })
        return rows[0] if rows else None


ledger_repo = LedgerRepository()
