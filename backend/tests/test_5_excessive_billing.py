import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_5_excessive_billing(client: AsyncClient, clinic_staff_headers: dict):
    """TEST 5: Excessive billing.
    - Submit an amount above the program cap (max_amount_per_visit is 5000.00).
    - Ensure policy rejection in Stage 3.
    """
    encounter_payload = {
        "program_id": "40000000-0000-4000-8000-000000000001",
        "patient_ref": "DEMO-PATIENT-001",
        "device_id": "50000000-0000-4000-8000-000000000001",
        "device_fingerprint": "DEMO-DEVICE-FINGERPRINT-001",
        "treatment_code": "MATERNAL_CARE",
        "amount": "8500.00",  # Exceeds KES 5,000 cap
        "currency": "KES",
        "occurred_at": "2026-11-22T10:00:00+03:00",
        "idempotency_key": str(uuid.uuid4()),
        "offline_created": False
    }

    # 1. Submit encounter
    resp = await client.post("/api/v1/encounters", json=encounter_payload, headers=clinic_staff_headers)
    assert resp.status_code == 201
    encounter_id = resp.json()["encounter_id"]
    otp = resp.json()["message"].split("DEMO OTP:")[1].strip()

    # 2. Confirm consent OTP - Stage 3 policy validation should reject excessive billing
    consent_resp = await client.post(
        f"/api/v1/encounters/{encounter_id}/consent",
        json={"otp": otp},
        headers=clinic_staff_headers
    )
    assert consent_resp.status_code == 200
    res = consent_resp.json()
    assert res["status"] == "rejected"
    assert any("AMOUNT_EXCEEDS_CAP" in r for r in res.get("reasons", []))
