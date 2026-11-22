import asyncio
import random
import secrets
from datetime import datetime, timezone
from app.core.config import settings
from app.core.security import sign_callback_payload, verify_callback_signature
from app.core.logging import safe_logger


class MockMpesa:
    """Simulated Safaricom Daraja B2C / B2B Settlement Gateway.
    Moves no real money. Provides realistic latency, response schemas, and callback verification.
    """

    async def disburse(self, *, phone: str, amount: str, currency: str, reference: str) -> dict:
        if settings.mpesa_mode != "mock":
            raise RuntimeError("Only mock settlement mode is enabled for this MVP")

        # Simulate provider network latency
        if settings.mock_mpesa_latency_ms > 0:
            await asyncio.sleep(settings.mock_mpesa_latency_ms / 1000)

        # Simulate provider-side random failure if configured
        if settings.mock_mpesa_failure_rate > 0 and random.random() < settings.mock_mpesa_failure_rate:
            safe_logger.warning(f"Simulated M-Pesa failure triggered for reference {reference}")
            return {
                "success": False,
                "result_code": "2001",
                "result_desc": "The initiator information is invalid (Simulated Provider Rejection)",
                "reference": reference,
                "amount": amount,
                "currency": currency,
            }

        tx_id = f"NENA{secrets.token_hex(6).upper()}"
        phone_masked = f"******{phone[-3:]}" if len(phone) >= 3 else "***"

        return {
            "success": True,
            "result_code": "0",
            "result_desc": "The service request is processed successfully.",
            "transaction_id": tx_id,
            "amount": amount,
            "currency": currency,
            "phone_masked": phone_masked,
            "reference": reference,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    def verify_callback(self, payload_bytes: bytes, signature_header: str) -> bool:
        """Verifies Safaricom Daraja webhook callback signature."""
        return verify_callback_signature(payload_bytes, signature_header)


mpesa = MockMpesa()
