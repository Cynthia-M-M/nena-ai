import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_2_duplicate_claim(client: AsyncClient, clinic_staff_headers: dict):
    """TEST 2: Duplicate claim.
    - Submit an encounter twice.
    - Ensure idempotency prevents duplicate claim and duplicate payment.
    """
    idempotency_key = str(uuid.uuid4())
    encounter_payload = {
        "program_id": "40000000-0000-4000-8000-000000000001",
        "patient_ref": "DEMO-PATIENT-001",
        "device_id": "50000000-0000-4000-8000-000000000001",
        "device_fingerprint": "DEMO-DEVICE-FINGERPRINT-001",
        "treatment_code": "MALARIA_LAB",
        "description": "Malaria test",
        "amount": "1200.00",
        "currency": "KES",
        "occurred_at": "2026-11-22T10:00:00+03:00",
        "idempotency_key": idempotency_key,
        "offline_created": False
    }

    # First submission
    resp1 = await client.post("/api/v1/encounters", json=encounter_payload, headers=clinic_staff_headers)
    assert resp1.status_code == 201

    # Second submission with the exact same idempotency_key
    resp2 = await client.post("/api/v1/encounters", json=encounter_payload, headers=clinic_staff_headers)
    assert resp2.status_code == 409
    assert "idempotency key" in resp2.json()["message"].lower()
