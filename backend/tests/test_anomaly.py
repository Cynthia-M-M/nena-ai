import pytest
from app.services.anomaly import AnomalyDetector


@pytest.mark.asyncio
async def test_normal_claim_low_risk():
    detector = AnomalyDetector()
    encounter = {
        "amount": "1200.00",
        "patient_token_id": "p1",
        "treatment_code": "MALARIA_LAB",
        "clinic_organization_id": "c1",
        "occurred_at": "2026-11-22T10:00:00+00:00"
    }
    result = await detector.assess(encounter, [], {"county": "Nairobi"})
    assert result["risk_score"] == 0
    assert result["risk_level"] == "low"
    assert result["recommended_action"] == "approve"


@pytest.mark.asyncio
async def test_duplicate_claim_is_flagged():
    detector = AnomalyDetector()
    encounter = {
        "amount": "1200.00",
        "patient_token_id": "p1",
        "treatment_code": "MALARIA_LAB",
        "clinic_organization_id": "c1",
        "occurred_at": "2026-11-22T10:00:00+00:00"
    }
    result = await detector.assess(encounter, [encounter], {"county": "Nairobi"})
    assert "POSSIBLE_DUPLICATE" in [x["code"] for x in result["flags"]]
    assert result["risk_score"] >= 40
    assert result["recommended_action"] == "manual_audit"


@pytest.mark.asyncio
async def test_off_hours_and_high_value_spike():
    detector = AnomalyDetector()
    encounter = {
        "amount": "4500.00",
        "patient_token_id": "p1",
        "treatment_code": "MATERNAL_CARE",
        "clinic_organization_id": "c1",
        "occurred_at": "2026-11-22T02:30:00+00:00"  # 02:30 AM
    }
    result = await detector.assess(encounter, [], {"county": "Nairobi"})
    flags = [x["code"] for x in result["flags"]]
    assert "HIGH_VALUE_CLAIM" in flags
    assert "UNUSUAL_HOUR" in flags
    assert result["risk_score"] >= 30
