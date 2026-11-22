import pytest
import uuid
from httpx import AsyncClient
from app.core.database import db


@pytest.mark.asyncio
async def test_9_ledger_tampering(client: AsyncClient, clinic_staff_headers: dict, auditor_headers: dict):
    """TEST 9: Ledger tampering & cryptographic chain verification.
    - Successfully process two valid transactions.
    - Run chain verification -> confirms chain is valid.
    - Simulate malicious direct tampering of an amount in a past ledger entry.
    - Re-run chain verification -> detects corrupted hash and broken chain links.
    """
    # 1. Process transaction 1
    p1 = {
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
    r1 = await client.post("/api/v1/encounters", json=p1, headers=clinic_staff_headers)
    eid1 = r1.json()["encounter_id"]
    otp1 = r1.json()["message"].split("DEMO OTP:")[1].strip()
    await client.post(f"/api/v1/encounters/{eid1}/consent", json={"otp": otp1}, headers=clinic_staff_headers)

    # 2. Process transaction 2
    p2 = {
        "program_id": "40000000-0000-4000-8000-000000000001",
        "patient_ref": "DEMO-PATIENT-002",
        "device_id": "50000000-0000-4000-8000-000000000001",
        "device_fingerprint": "DEMO-DEVICE-FINGERPRINT-001",
        "treatment_code": "PEDIATRIC_EMERGENCY",
        "amount": "2500.00",
        "currency": "KES",
        "occurred_at": "2026-11-22T10:05:00+03:00",
        "idempotency_key": str(uuid.uuid4()),
        "offline_created": False
    }
    r2 = await client.post("/api/v1/encounters", json=p2, headers=clinic_staff_headers)
    eid2 = r2.json()["encounter_id"]
    otp2 = r2.json()["message"].split("DEMO OTP:")[1].strip()
    await client.post(f"/api/v1/encounters/{eid2}/consent", json={"otp": otp2}, headers=clinic_staff_headers)

    # 3. Verify clean chain
    v_clean = await client.post("/api/v1/ledger/verify", headers=auditor_headers)
    assert v_clean.status_code == 200
    assert v_clean.json()["verified"] is True
    assert v_clean.json()["total_entries"] == 2
    assert len(v_clean.json()["inconsistencies"]) == 0

    # 4. Malicious tampering: directly modify the amount in entry 1
    tampered_entry = db._mock.tables["ledger_entries"][0]
    tampered_entry["amount"] = "99999.00"

    # 5. Re-run chain verification: must detect tamper!
    v_tampered = await client.post("/api/v1/ledger/verify", headers=auditor_headers)
    assert v_tampered.status_code == 200
    assert v_tampered.json()["verified"] is False
    inconsistencies = v_tampered.json()["inconsistencies"]
    assert len(inconsistencies) > 0
    errors = [inc["error"] for inc in inconsistencies]
    assert "TX_HASH_CORRUPTION" in errors
