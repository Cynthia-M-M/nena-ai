from fastapi import APIRouter, Depends
from app.core.auth import Principal, get_principal, require_membership
from app.schemas.ledger import LedgerEntryResponse, LedgerChainVerifyResponse, LedgerReversalRequest
from app.services.ledger import ledger_service

router = APIRouter(prefix="/ledger", tags=["Immutable Financial Ledger"])


@router.get("", response_model=list[LedgerEntryResponse])
async def get_ledger(principal: Principal = Depends(get_principal)):
    """Returns an immutable append-only feed of recent financial events."""
    return await ledger_service.get_ledger_feed()


@router.post("/verify", response_model=LedgerChainVerifyResponse)
async def verify_chain(principal: Principal = Depends(get_principal)):
    """Executes cryptographic SHA-256 chain verification across all ledger transactions,
    detecting any tampering, modified amounts, or broken hash links.
    """
    return await ledger_service.verify_chain_integrity()


@router.post("/{ledger_id}/reverse")
async def reverse_entry(ledger_id: str, payload: LedgerReversalRequest, principal: Principal = Depends(get_principal)):
    """Appends an immutable compensating reversal event to restore program funds without mutating history."""
    return await ledger_service.reverse_transaction(ledger_id, payload.reason, principal.user_id)
