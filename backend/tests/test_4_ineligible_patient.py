import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_4_ineligible_patient(client: AsyncClient, clinic_staff_headers: dict):
    """TEST 4: Ineligible patient.
    - Use an expired subsidy voucher or unregistered patient reference.
    - Ensure rejection before encounter creation.
    """
    encounter_payload = {
        "program_id": "40000000-0000-4000-8000-000000000001",
        "patient_ref": "DEMO-PATIENT-EXPIRED",
        "device_id": "50000000-0000-4000-8000-000000000001",
        "device_fingerprint": "DEMO-DEVICE-FINGERPRINT-001",
        "treatment_code": "MALARIA_LAB",
        "amount": "1200.00",
        "currency": "KES",
        "occurred_at": "2026-11-22T10:00:00+03:00",
        "idempotency_key": str(uuid.uuid4()),
        "offline_created": False
    }

    resp = await client.post("/api/v1/encounters", json=encounter_payload, headers=clinic_staff_headers)
    assert resp.status_code == 403
    assert "No active subsidy coverage found" in resp.json()["message"]
