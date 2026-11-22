import pytest
import asyncio
import uuid
from httpx import AsyncClient
from app.core.database import db


@pytest.mark.asyncio
async def test_8_concurrent_transactions(client: AsyncClient, clinic_staff_headers: dict):
    """TEST 8: Concurrent transactions & overspend protection.
    - Submit two claims concurrently against limited funding (allocated 2000.00, claim 1200.00 each).
    - Ensure atomic row locking prevents overspending: exactly one succeeds and one fails.
    """
    await db.patch("funding_programs", {"id": "eq.40000000-0000-4000-8000-000000000001"}, {
        "allocated_amount": 2000.00
    })

    # Prepare claim 1 (patient 1)
    claim1 = {
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
    r1 = await client.post("/api/v1/encounters", json=claim1, headers=clinic_staff_headers)
    eid1 = r1.json()["encounter_id"]
    otp1 = r1.json()["message"].split("DEMO OTP:")[1].strip()

    # Prepare claim 2 (patient 2)
    claim2 = {
        "program_id": "40000000-0000-4000-8000-000000000001",
        "patient_ref": "DEMO-PATIENT-002",
        "device_id": "50000000-0000-4000-8000-000000000001",
        "device_fingerprint": "DEMO-DEVICE-FINGERPRINT-001",
        "treatment_code": "PEDIATRIC_EMERGENCY",
        "amount": "1200.00",
        "currency": "KES",
        "occurred_at": "2026-11-22T10:05:00+03:00",
        "idempotency_key": str(uuid.uuid4()),
        "offline_created": False
    }
    r2 = await client.post("/api/v1/encounters", json=claim2, headers=clinic_staff_headers)
    eid2 = r2.json()["encounter_id"]
    otp2 = r2.json()["message"].split("DEMO OTP:")[1].strip()

    # Authorize both claims concurrently
    res1, res2 = await asyncio.gather(
        client.post(f"/api/v1/encounters/{eid1}/consent", json={"otp": otp1}, headers=clinic_staff_headers),
        client.post(f"/api/v1/encounters/{eid2}/consent", json={"otp": otp2}, headers=clinic_staff_headers),
        return_exceptions=True
    )

    statuses = [res1.status_code, res2.status_code]
    assert 200 in statuses, "At least one transaction must succeed"
    assert 409 in statuses, "The concurrent transaction exceeding available funds must be rejected"
