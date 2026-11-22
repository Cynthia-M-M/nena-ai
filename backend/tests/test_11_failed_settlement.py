import pytest
import uuid
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_11_failed_settlement(client: AsyncClient, clinic_staff_headers: dict, monkeypatch):
    """TEST 11: Failed settlement handling.
    - Simulate an M-Pesa provider failure during disbursement.
    - Ensure no false successful payout is recorded.
    - Verify encounter status remains 'settlement_pending' for reconciliation.
    """
    # Force mock M-Pesa failure rate to 100%
    monkeypatch.setattr(settings, "mock_mpesa_failure_rate", 1.0)

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
    eid = resp.json()["encounter_id"]
    otp = resp.json()["message"].split("DEMO OTP:")[1].strip()

    # Attempt consent & settlement
    settle_resp = await client.post(
        f"/api/v1/encounters/{eid}/consent",
        json={"otp": otp},
        headers=clinic_staff_headers
    )
    assert settle_resp.status_code == 200
    res = settle_resp.json()
    assert res["status"] == "settlement_pending"
    assert "Settlement rejected by provider" in res["message"]

    # Verify encounter status is settlement_pending, NEVER settled
    get_resp = await client.get(f"/api/v1/encounters/{eid}", headers=clinic_staff_headers)
    assert get_resp.json()["status"] == "settlement_pending"
