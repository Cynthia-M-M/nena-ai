from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.core.database import db

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


@router.get("")
async def health_check():
    """Health-check endpoint validating API status and database connectivity."""
    db_status = "connected"
    head_hash = "0" * 64
    try:
        state = await db.select("ledger_chain_state", {"select": "last_hash", "id": "eq.1", "limit": "1"})
        if state:
            head_hash = state[0]["last_hash"]
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "version": "0.2.0",
        "database": db_status,
        "ledger_chain_head": head_hash,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
