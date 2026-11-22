from app.repositories.ledger_repository import ledger_repo


class LedgerService:
    """Manages immutable ledger operations, atomic reservations, and chain verification."""

    async def get_ledger_feed(self, limit: int = 50) -> list[dict]:
        return await ledger_repo.list_all({
            "select": "id,encounter_id,program_id,clinic_organization_id,funder_organization_id,event_type,amount,currency,prev_hash,tx_hash,metadata,created_by,created_at",
            "order": "created_at.desc",
            "limit": str(limit)
        })

    async def verify_chain_integrity(self) -> dict:
        return await ledger_repo.verify_chain()

    async def reverse_transaction(self, ledger_id: str, reason: str, actor_id: str) -> dict:
        return await ledger_repo.reverse_entry(ledger_id, reason, actor_id)


ledger_service = LedgerService()
