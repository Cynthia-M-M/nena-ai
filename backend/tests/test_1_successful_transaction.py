import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_1_successful_transaction(client: AsyncClient, clinic_staff_headers: dict):
    """TEST 1: Successful end-to-end transaction.
    - Valid clinic.
    - Registered device.
    - Active patient coverage.
    - Valid OTP.
    - Valid treatment.
    - Sufficient funding.
    - Low anomaly score.
    - Ledger authorization succeeds.
    - Mock M-Pesa payout completes.
    """
    idempotency_key = str(uuid.uuid4())
    encounter_payload = {
        "program_id": "40000000-0000-4000-8000-000000000001",
        "patient_ref": "DEMO-PATIENT-001",
        "device_id": "50000000-0000-4000-8000-000000000001",
        "device_fingerprint": "DEMO-DEVICE-FINGERPRINT-001",
        "treatment_code": "MALARIA_LAB",
        "description": "Rapid malaria antigen blood film test",
        "amount": "1200.00",
        "currency": "KES",
        "occurred_at": "2026-11-22T10:00:00+03:00",
        "idempotency_key": idempotency_key,
        "offline_created": False
    }

    # 1. Submit Encounter
    resp = await client.post("/api/v1/encounters", json=encounter_payload, headers=clinic_staff_headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    encounter_id = data["encounter_id"]
    assert data["status"] == "pending_verification"
    assert data["consent_required"] is True
    assert "DEMO OTP:" in data["message"]
    otp = data["message"].split("DEMO OTP:")[1].strip()

    # 2. Confirm Patient Consent with OTP
    consent_resp = await client.post(
        f"/api/v1/encounters/{encounter_id}/consent",
        json={"otp": otp},
        headers=clinic_staff_headers
    )
    assert consent_resp.status_code == 200, consent_resp.text
    settlement_data = consent_resp.json()

    # 3. Verify settlement & payout completion
    assert settlement_data["status"] == "settled"
    assert settlement_data["provider"] == "MPESA_MOCK"
    assert settlement_data["provider_transaction_id"].startswith("NENA")
    assert settlement_data["amount"] == "1200.00"

    # 4. Verify encounter status in database
    get_resp = await client.get(f"/api/v1/encounters/{encounter_id}", headers=clinic_staff_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "settled"

    # 5. Verify audit evidence & ledger chain
    audit_resp = await client.get(f"/api/v1/audit/encounters/{encounter_id}", headers=clinic_staff_headers)
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert len(audit_data["verification_events"]) == 4
    stages = [ev["stage"] for ev in audit_data["verification_events"]]
    assert "identity_device" in stages
    assert "patient_consent" in stages
    assert "program_policy" in stages
    assert "anomaly_detection" in stages
    assert len(audit_data["ledger"]) == 1
    assert audit_data["ledger"][0]["event_type"] == "subsidy_authorized"
    assert float(audit_data["ledger"][0]["amount"]) == 1200.00
    assert len(audit_data["payouts"]) == 1
    assert audit_data["payouts"][0]["status"] == "completed"
