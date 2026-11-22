import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_6_fraudulent_activity(client: AsyncClient, clinic_staff_headers: dict, auditor_headers: dict):
    """TEST 6: Fraudulent / suspicious activity.
    - Submit suspicious repeated claims for the same patient and service.
    - Ensure anomaly detection scores high risk and routes claim to MANUAL_AUDIT.
    - Verify claim is not paid out automatically.
    - Verify manual audit review workflow (Auditor approves or rejects).
    """
    # 1. Submit and settle the first legitimate claim
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
    await client.post(f"/api/v1/encounters/{eid1}/consent", json={"otp": otp1}, headers=clinic_staff_headers)

    # 2. Submit a suspicious rapid duplicate claim for the same patient and same treatment
    claim2 = {
        "program_id": "40000000-0000-4000-8000-000000000001",
        "patient_ref": "DEMO-PATIENT-001",
        "device_id": "50000000-0000-4000-8000-000000000001",
        "device_fingerprint": "DEMO-DEVICE-FINGERPRINT-001",
        "treatment_code": "MALARIA_LAB",
        "amount": "1200.00",
        "currency": "KES",
        "occurred_at": "2026-11-22T10:15:00+03:00",
        "idempotency_key": str(uuid.uuid4()),
        "offline_created": False
    }
    r2 = await client.post("/api/v1/encounters", json=claim2, headers=clinic_staff_headers)
    eid2 = r2.json()["encounter_id"]
    otp2 = r2.json()["message"].split("DEMO OTP:")[1].strip()

    # Verify consent on second claim: anomaly detector flags duplicate (+55 risk score >= 40 threshold)
    c2 = await client.post(f"/api/v1/encounters/{eid2}/consent", json={"otp": otp2}, headers=clinic_staff_headers)
    assert c2.status_code == 200
    res2 = c2.json()
    assert res2["status"] == "manual_audit"
    assert res2["risk_score"] >= 40
    assert "manual audit" in res2["message"].lower()

    # 3. Verify it is listed in manual audit queue
    audit_queue = await client.get("/api/v1/audit/encounters", headers=auditor_headers)
    assert audit_queue.status_code == 200
    flagged_ids = [e["id"] for e in audit_queue.json()]
    assert eid2 in flagged_ids

    # 4. Auditor reviews and rejects the fraudulent claim
    decision_resp = await client.post(
        f"/api/v1/audit/encounters/{eid2}/decision",
        json={"decision": "reject", "reason": "Patient confirmed duplicate submission was an error."},
        headers=auditor_headers
    )
    assert decision_resp.status_code == 200
    assert decision_resp.json()["status"] == "rejected"
