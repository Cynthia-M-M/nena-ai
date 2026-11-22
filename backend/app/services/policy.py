from datetime import datetime, timezone
from decimal import Decimal
from app.repositories.program_repository import program_repo
from app.core.errors import ConflictError, ForbiddenError


class PolicyService:
    """Evaluates Stage 3 Programmatic Policy Rules."""

    async def validate_encounter_policy(self, encounter: dict, clinic: dict, recent_claims: list[dict]) -> tuple[bool, list[str]]:
        program_id = encounter["program_id"]
        amount = Decimal(str(encounter["amount"]))
        rules = await program_repo.get_active_rules(program_id)
        if not rules:
            raise ConflictError("Funding program has no active rules")

        policy_reasons: list[str] = []

        # 1. Cap check
        max_visit = Decimal(str(rules["max_amount_per_visit"]))
        if amount > max_visit:
            policy_reasons.append(f"AMOUNT_EXCEEDS_CAP: amount {amount} > max allowed {max_visit}")

        # 2. Approved treatment code check
        if encounter["treatment_code"] not in rules["approved_treatment_codes"]:
            policy_reasons.append(f"TREATMENT_NOT_COVERED: {encounter['treatment_code']} not in approved list")

        # 3. Allowed county check
        clinic_county = clinic.get("county", "")
        if clinic_county not in rules["allowed_counties"]:
            policy_reasons.append(f"COUNTY_NOT_ALLOWED: clinic county '{clinic_county}' not in {rules['allowed_counties']}")

        # 4. Daily clinic claim limit check
        today_clinic_claims = [
            c for c in recent_claims
            if c.get("clinic_organization_id") == encounter["clinic_organization_id"]
        ]
        if len(today_clinic_claims) >= rules.get("max_daily_claims", 250):
            policy_reasons.append("MAX_DAILY_CLAIMS_EXCEEDED")

        # 5. Daily household claim limit check
        same_patient_claims = [
            c for c in recent_claims
            if c.get("patient_token_id") == encounter["patient_token_id"]
        ]
        if len(same_patient_claims) >= rules.get("max_household_claims_per_day", 3):
            policy_reasons.append("MAX_HOUSEHOLD_DAILY_CLAIMS_EXCEEDED")

        is_valid = len(policy_reasons) == 0
        return is_valid, policy_reasons


policy_service = PolicyService()
