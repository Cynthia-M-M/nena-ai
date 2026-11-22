import pytest
import uuid
from httpx import AsyncClient
from app.core.database import db


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.2.0"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_programs_and_rules_endpoints(client: AsyncClient, funder_headers: dict):
    # 1. List programs
    resp = await client.get("/api/v1/programs", headers=funder_headers)
    assert resp.status_code == 200
    programs = resp.json()
    assert len(programs) >= 1
    program_id = programs[0]["id"]

    # 2. Get program detail
    detail_resp = await client.get(f"/api/v1/programs/{program_id}", headers=funder_headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == program_id
    assert detail_resp.json()["active_rules"] is not None

    # 3. Update program rules (version bump)
    update_payload = {
        "max_amount_per_visit": 6000.00,
        "approved_treatment_codes": ["MATERNAL_CARE", "PEDIATRIC_EMERGENCY", "MALARIA_LAB"],
        "allowed_counties": ["Nairobi", "Kisumu", "Mombasa"],
        "requires_patient_otp": True,
        "max_daily_claims": 300,
        "max_household_claims_per_day": 4
    }
    put_resp = await client.put(f"/api/v1/programs/{program_id}/rules", json=update_payload, headers=funder_headers)
    assert put_resp.status_code == 200
    new_rule = put_resp.json()
    assert new_rule["version"] == 2
    assert float(new_rule["max_amount_per_visit"]) == 6000.00


@pytest.mark.asyncio
async def test_dashboards(client: AsyncClient, funder_headers: dict, clinic_staff_headers: dict):
    funder_id = "10000000-0000-4000-8000-000000000001"
    clinic_id = "20000000-0000-4000-8000-000000000001"

    # Funder dashboard
    f_resp = await client.get(f"/api/v1/dashboard/funder/{funder_id}", headers=funder_headers)
    assert f_resp.status_code == 200
    f_data = f_resp.json()
    assert f_data["funder_organization_id"] == funder_id
    assert "regional_breakdown" in f_data
    assert "Nairobi" in f_data["regional_breakdown"]
    assert "Kisumu" in f_data["regional_breakdown"]
    assert "Mombasa" in f_data["regional_breakdown"]

    # Clinic dashboard
    c_resp = await client.get(f"/api/v1/dashboard/clinic/{clinic_id}", headers=clinic_staff_headers)
    assert c_resp.status_code == 200
    c_data = c_resp.json()
    assert c_data["clinic_organization_id"] == clinic_id
    assert c_data["county"] == "Nairobi"


@pytest.mark.asyncio
async def test_device_management(client: AsyncClient, clinic_staff_headers: dict, platform_admin_headers: dict):
    clinic_id = "20000000-0000-4000-8000-000000000001"

    # List devices
    dev_resp = await client.get(f"/api/v1/clinics/{clinic_id}/devices", headers=clinic_staff_headers)
    assert dev_resp.status_code == 200
    devices = dev_resp.json()
    assert len(devices) >= 1

    # Register new device (platform admin / clinic admin)
    reg_payload = {
        "device_name": "Emergency Ward Tablet 3",
        "device_fingerprint": "UNIQUE-HARDWARE-FINGERPRINT-SAMPLE-12345"
    }
    reg_resp = await client.post(f"/api/v1/clinics/{clinic_id}/devices", json=reg_payload, headers=platform_admin_headers)
    assert reg_resp.status_code == 200
    new_device = reg_resp.json()
    assert new_device["device_name"] == "Emergency Ward Tablet 3"
    assert new_device["active"] is True

    # Revoke device
    rev_resp = await client.delete(f"/api/v1/clinics/{clinic_id}/devices/{new_device['id']}", headers=platform_admin_headers)
    assert rev_resp.status_code == 200
    assert rev_resp.json()["revoked"] is True


@pytest.mark.asyncio
async def test_ledger_reversal_procedure(client: AsyncClient, clinic_staff_headers: dict, auditor_headers: dict, platform_admin_headers: dict):
    # 1. Process valid claim
    claim = {
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
    r = await client.post("/api/v1/encounters", json=claim, headers=clinic_staff_headers)
    eid = r.json()["encounter_id"]
    otp = r.json()["message"].split("DEMO OTP:")[1].strip()
    await client.post(f"/api/v1/encounters/{eid}/consent", json={"otp": otp}, headers=clinic_staff_headers)

    # 2. Get ledger entry
    feed_resp = await client.get("/api/v1/ledger", headers=auditor_headers)
    assert feed_resp.status_code == 200
    entries = feed_resp.json()
    assert len(entries) >= 1
    orig_entry = entries[0]

    # 3. Reverse entry using compensating reversal
    rev_resp = await client.post(
        f"/api/v1/ledger/{orig_entry['id']}/reverse",
        json={"reason": "Compensating entry: clinical cancellation requested."},
        headers=platform_admin_headers
    )
    assert rev_resp.status_code == 200
    rev_data = rev_resp.json()
    assert "reversal_ledger_id" in rev_data
    assert float(rev_data["restored_amount"]) == 1200.00

    # 4. Verify chain integrity still passes with reversal entry
    v_resp = await client.post("/api/v1/ledger/verify", headers=auditor_headers)
    assert v_resp.status_code == 200
    assert v_resp.json()["verified"] is True
