import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_3_invalid_otp(client: AsyncClient, clinic_staff_headers: dict):
    """TEST 3: Invalid OTP.
    - Submit incorrect OTP.
    - Ensure the claim cannot proceed to authorization or settlement.
    """
    encounter_payload = {
        "program_id": "40000000-0000-4000-8000-000000000001",
        "patient_ref": "DEMO-PATIENT-001",
        "device_id": "50000000-0000-4000-8000-000000000001",
        "device_fingerprint": "DEMO-DEVICE-FINGERPRINT-001",
        "treatment_code": "MALARIA_LAB",
        "amount": "1200.00",
        "currency": "KES",
        "occurred_at": "2026-11-22T10:00:00+03:00",
        "idempotency_key": str(uuid.uuid4()),
        "offline_created": False
    }

    # Submit encounter
    resp = await client.post("/api/v1/encounters", json=encounter_payload, headers=clinic_staff_headers)
    assert resp.status_code == 201
    encounter_id = resp.json()["encounter_id"]

    # Attempt verification with WRONG OTP
    bad_otp_resp = await client.post(
        f"/api/v1/encounters/{encounter_id}/consent",
        json={"otp": "000000"},
        headers=clinic_staff_headers
    )
    assert bad_otp_resp.status_code == 403
    assert "Invalid OTP" in bad_otp_resp.json()["message"]

    # Verify encounter status remains pending_verification
    get_resp = await client.get(f"/api/v1/encounters/{encounter_id}", headers=clinic_staff_headers)
    assert get_resp.json()["status"] == "pending_verification"
