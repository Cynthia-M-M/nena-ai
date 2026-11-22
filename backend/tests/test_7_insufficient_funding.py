import pytest
import uuid
from httpx import AsyncClient
from app.core.database import db


@pytest.mark.asyncio
async def test_7_insufficient_funding(client: AsyncClient, clinic_staff_headers: dict):
    """TEST 7: Insufficient funding.
    - Submit a valid claim against a funding program whose budget is exhausted.
    - Ensure atomic authorization fails and no payout is released.
    """
    # Temporarily set program allocated_amount to a low value
    await db.patch("funding_programs", {"id": "eq.40000000-0000-4000-8000-000000000001"}, {
        "allocated_amount": 500.00  # Only KES 500 allocated
    })

    encounter_payload = {
        "program_id": "40000000-0000-4000-8000-000000000001",
        "patient_ref": "DEMO-PATIENT-001",
        "device_id": "50000000-0000-4000-8000-000000000001",
        "device_fingerprint": "DEMO-DEVICE-FINGERPRINT-001",
        "treatment_code": "MALARIA_LAB",
        "amount": "1200.00",  # Exceeds remaining budget
        "currency": "KES",
        "occurred_at": "2026-11-22T10:00:00+03:00",
        "idempotency_key": str(uuid.uuid4()),
        "offline_created": False
    }

    # 1. Submit encounter
    resp = await client.post("/api/v1/encounters", json=encounter_payload, headers=clinic_staff_headers)
    assert resp.status_code == 201
    eid = resp.json()["encounter_id"]
    otp = resp.json()["message"].split("DEMO OTP:")[1].strip()

    # 2. Confirm consent - atomic authorization should fail due to insufficient uncommitted funds
    consent_resp = await client.post(
        f"/api/v1/encounters/{eid}/consent",
        json={"otp": otp},
        headers=clinic_staff_headers
    )
    assert consent_resp.status_code == 409
    assert "insufficient uncommitted program funds" in consent_resp.json()["message"].lower()
