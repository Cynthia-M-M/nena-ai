import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_12_offline_synchronization(client: AsyncClient, clinic_staff_headers: dict):
    """TEST 12: Offline synchronization.
    - Submit an encounter marked offline_created=True from an IndexedDB sync queue.
    - Ensure it undergoes full server-side verification before ledger authorization.
    """
    idempotency_key = str(uuid.uuid4())
    encounter_payload = {
        "program_id": "40000000-0000-4000-8000-000000000001",
        "patient_ref": "DEMO-PATIENT-001",
        "device_id": "50000000-0000-4000-8000-000000000001",
        "device_fingerprint": "DEMO-DEVICE-FINGERPRINT-001",
        "treatment_code": "PEDIATRIC_EMERGENCY",
        "amount": "2500.00",
        "currency": "KES",
        "occurred_at": "2026-11-22T08:30:00+03:00",
        "idempotency_key": idempotency_key,
        "offline_created": True  # Flagged as queued offline
    }

    # 1. Synchronize offline encounter to server
    resp = await client.post("/api/v1/encounters", json=encounter_payload, headers=clinic_staff_headers)
    assert resp.status_code == 201
    data = resp.json()
    eid = data["encounter_id"]
    otp = data["message"].split("DEMO OTP:")[1].strip()

    # 2. Complete verification & settlement
    consent_resp = await client.post(
        f"/api/v1/encounters/{eid}/consent",
        json={"otp": otp},
        headers=clinic_staff_headers
    )
    assert consent_resp.status_code == 200
    assert consent_resp.json()["status"] == "settled"

    # 3. Verify record in database retains offline_created=True
    get_resp = await client.get(f"/api/v1/encounters/{eid}", headers=clinic_staff_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["offline_created"] is True
