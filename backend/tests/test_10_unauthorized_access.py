import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_10_unauthorized_access(client: AsyncClient, clinic_staff_headers: dict, clinic_b_headers: dict):
    """TEST 10: Unauthorized cross-tenant access.
    - Clinic A staff submits an encounter.
    - Clinic B staff attempts to read Clinic A's encounter.
    - Clinic B staff attempts to submit patient consent for Clinic A's encounter.
    - Verify access is strictly denied with HTTP 403 Forbidden.
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

    # Clinic A submits
    resp = await client.post("/api/v1/encounters", json=encounter_payload, headers=clinic_staff_headers)
    assert resp.status_code == 201
    eid = resp.json()["encounter_id"]
    otp = resp.json()["message"].split("DEMO OTP:")[1].strip()

    # Clinic B attempts to view Clinic A's encounter
    view_resp = await client.get(f"/api/v1/encounters/{eid}", headers=clinic_b_headers)
    assert view_resp.status_code == 403
    assert "Active organization membership required" in view_resp.json()["message"]

    # Clinic B attempts to confirm consent for Clinic A's encounter
    consent_resp = await client.post(
        f"/api/v1/encounters/{eid}/consent",
        json={"otp": otp},
        headers=clinic_b_headers
    )
    assert consent_resp.status_code == 403
