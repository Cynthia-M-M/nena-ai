from datetime import datetime
from decimal import Decimal
from app.core.config import settings


class AnomalyDetector:
    """Explainable heuristic scoring engine; not a trained clinical or ML fraud model.
    Evaluates risk signals, produces deterministic integer scores (0-100), and provides
    transparent human-readable risk flags for audit.
    """

    async def assess(self, encounter: dict, recent_claims: list[dict], clinic: dict) -> dict:
        score = 0
        flags: list[dict] = []
        amount = Decimal(str(encounter["amount"]))

        # 1. Duplicate claim signal (same patient token & treatment code recently submitted)
        same_patient_service = [
            x for x in recent_claims
            if x.get("patient_token_id") == encounter.get("patient_token_id")
            and x.get("treatment_code") == encounter.get("treatment_code")
        ]
        if same_patient_service:
            score += 55
            flags.append({
                "code": "POSSIBLE_DUPLICATE",
                "weight": 55,
                "description": "Patient token has a recent claim with identical treatment code"
            })

        # 2. Clinic claim velocity signal
        same_clinic = [
            x for x in recent_claims
            if x.get("clinic_organization_id") == encounter.get("clinic_organization_id")
        ]
        if len(same_clinic) >= 25:
            score += 15
            flags.append({
                "code": "HIGH_CLAIM_VELOCITY",
                "weight": 15,
                "description": f"High submission velocity: {len(same_clinic)} claims in observation window"
            })

        # 3. High value claim spike signal
        if amount > Decimal("4000"):
            score += 15
            flags.append({
                "code": "HIGH_VALUE_CLAIM",
                "weight": 15,
                "description": f"Claim amount KES {amount} is in top 95th percentile (> KES 4,000)"
            })

        # 4. Unusual off-hours activity signal (between 23:00 and 05:00)
        occurred_raw = encounter["occurred_at"]
        if isinstance(occurred_raw, str):
            occurred = datetime.fromisoformat(occurred_raw.replace("Z", "+00:00"))
        else:
            occurred = occurred_raw
        if occurred.hour < 5 or occurred.hour >= 23:
            score += 15
            flags.append({
                "code": "UNUSUAL_HOUR",
                "weight": 15,
                "description": f"Claim occurred during off-hours ({occurred.hour:02d}:00)"
            })

        # 5. Geolocation verification signal
        county = clinic.get("county")
        if not county:
            score += 10
            flags.append({
                "code": "LOCATION_UNVERIFIED",
                "weight": 10,
                "description": "Facility has unverified or missing regional county coordinates"
            })

        score = min(score, 100)

        # Classification against configured thresholds
        if score >= settings.anomaly_reject_threshold:
            action, level = "reject", "critical"
        elif score >= settings.anomaly_manual_review_threshold:
            action, level = "manual_audit", "high" if score >= 65 else "medium"
        else:
            action, level = "approve", "low"

        return {
            "risk_score": score,
            "risk_level": level,
            "flags": flags,
            "recommended_action": action
        }


anomaly_detector = AnomalyDetector()
