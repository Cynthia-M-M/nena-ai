from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from app.core.config import settings
from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.core.security import keyed_hash, generate_otp, hash_otp, constant_time_equal
from app.repositories.clinic_repository import clinic_repo
from app.repositories.encounter_repository import encounter_repo
from app.repositories.program_repository import program_repo
from app.services.anomaly import anomaly_detector
from app.services.policy import policy_service
from app.integrations.sms_mock import sms_gateway


class VerificationService:
    """Four-Stage Zero-Trust Verification Engine Orchestrator."""

    async def submit_encounter(self, payload: dict, principal, clinic_org_id: str) -> dict:
        # STAGE 1: Identity & Device Authentication
        clinic = await clinic_repo.get_profile(clinic_org_id)
        if not clinic or clinic["verification_status"] != "verified":
            raise ForbiddenError("Clinic is not verified to submit claims")

        device_id = str(payload["device_id"])
        device = await clinic_repo.get_device(device_id, clinic_org_id)
        if not device or not device["active"]:
            raise ForbiddenError("Registered active clinic device is required")

        expected_device_hash = keyed_hash(payload["device_fingerprint"], "device-fingerprint")
        if not constant_time_equal(device["device_fingerprint_hash"], expected_device_hash):
            raise ForbiddenError("Device fingerprint mismatch; untrusted hardware attestation")

        # Program & Enrollment Verification
        program_id = str(payload["program_id"])
        program = await program_repo.get_by_id(program_id)
        if not program or not program["active"]:
            raise NotFoundError("Active funding program not found")

        enrollment = await program_repo.get_clinic_enrollment(program_id, clinic_org_id)
        if not enrollment or not enrollment["active"]:
            raise ForbiddenError("Clinic is not enrolled in this funding program")

        # Patient Coverage Verification
        patient = await program_repo.get_patient_token(program_id, payload["patient_ref"])
        if not patient or patient["coverage_status"] != "active":
            raise ForbiddenError("No active subsidy coverage found for patient reference")

        now = datetime.now(timezone.utc)
        if patient.get("valid_until"):
            valid_until = datetime.fromisoformat(patient["valid_until"].replace("Z", "+00:00"))
            if valid_until < now:
                raise ForbiddenError("Patient subsidy coverage has expired")

        if payload["currency"] != program["currency"]:
            raise ConflictError(f"Encounter currency ({payload['currency']}) must match funding program ({program['currency']})")

        occurred_at_dt = payload["occurred_at"]
        occurred_iso = occurred_at_dt.isoformat() if isinstance(occurred_at_dt, datetime) else occurred_at_dt

        # Insert encounter with county populated from clinic profile (resolves NOT NULL constraint)
        encounter_data = {
            "clinic_organization_id": clinic_org_id,
            "program_id": program_id,
            "patient_token_id": patient["id"],
            "submitted_by": principal.user_id,
            "device_id": device_id,
            "treatment_code": payload["treatment_code"],
            "description": payload.get("description"),
            "amount": str(payload["amount"]),
            "currency": payload["currency"],
            "county": clinic["county"],
            "occurred_at": occurred_iso,
            "submitted_at": now.isoformat(),
            "idempotency_key": str(payload["idempotency_key"]),
            "offline_created": payload.get("offline_created", False),
            "status": "pending_verification"
        }

        encounter = await encounter_repo.create(encounter_data)
        eid = encounter["id"]

        # Record Stage 1 Passed Event
        await encounter_repo.record_verification_event(
            encounter_id=eid,
            stage="identity_device",
            status="passed",
            reason_code="CLINIC_DEVICE_IDENTITY_AUTHENTICATED",
            details={"clinic_id": clinic_org_id, "device_id": device_id, "county": clinic["county"]}
        )

        # STAGE 2: Initiate Patient Consent Challenge
        otp = generate_otp()
        expires_at = datetime.fromtimestamp(now.timestamp() + settings.otp_ttl_seconds, timezone.utc)
        await encounter_repo.create_consent_challenge(
            encounter_id=eid,
            otp_hash=hash_otp(otp, eid),
            expires_at=expires_at
        )

        sms_result = await sms_gateway.send_otp(phone_masked="******001", otp=otp, challenge_id=eid)

        return {
            "encounter_id": eid,
            "status": "pending_verification",
            "consent_required": True,
            "message": sms_result["message"]
        }

    async def verify_consent_and_evaluate(self, encounter_id: str, otp: str, principal, clinic_org_id: str) -> dict:
        encounter = await encounter_repo.get_encounter(encounter_id)
        if not encounter:
            raise NotFoundError("Encounter not found")

        if encounter["clinic_organization_id"] != clinic_org_id:
            raise ForbiddenError("Encounter does not belong to your clinic")

        if encounter["submitted_by"] != principal.user_id:
            raise ForbiddenError("Only the submitting clinic staff can verify consent for this encounter")

        if encounter["status"] != "pending_verification":
            raise ConflictError(f"Encounter is not awaiting verification (status: {encounter['status']})")

        challenge = await encounter_repo.get_consent_challenge(encounter_id)
        if not challenge:
            raise NotFoundError("Consent challenge not found")

        if challenge.get("verified_at"):
            raise ConflictError("Consent challenge has already been verified")

        now = datetime.now(timezone.utc)
        expires_at = datetime.fromisoformat(challenge["expires_at"].replace("Z", "+00:00"))
        if expires_at < now:
            await encounter_repo.record_verification_event(encounter_id, "patient_consent", "failed", "OTP_EXPIRED")
            raise ForbiddenError("Consent challenge OTP has expired")

        attempts = int(challenge.get("attempts", 0))
        if attempts >= settings.otp_max_attempts:
            await encounter_repo.record_verification_event(encounter_id, "patient_consent", "failed", "MAX_ATTEMPTS_EXCEEDED")
            raise ForbiddenError("Maximum OTP verification attempts exceeded")

        expected_hash = hash_otp(otp, encounter_id)
        if not constant_time_equal(challenge["otp_hash"], expected_hash):
            await encounter_repo.update({"id": f"eq.{challenge['id']}"}, {"attempts": attempts + 1})
            await encounter_repo.record_verification_event(encounter_id, "patient_consent", "failed", "OTP_MISMATCH", {"attempts": attempts + 1})
            raise ForbiddenError("Invalid OTP; verification challenge failed")

        # Mark OTP Challenge as verified
        await encounter_repo.update({"id": f"eq.{challenge['id']}"}, {
            "verified_at": now.isoformat(),
            "attempts": attempts + 1
        })
        await encounter_repo.record_verification_event(encounter_id, "patient_consent", "passed", "PATIENT_CONSENT_CONFIRMED")

        # STAGE 3: Programmatic Policy Validation
        clinic = await clinic_repo.get_profile(clinic_org_id)
        recent_claims = await encounter_repo.get_recent_claims(encounter["program_id"], exclude_id=encounter_id)

        is_policy_valid, policy_reasons = await policy_service.validate_encounter_policy(encounter, clinic, recent_claims)
        if not is_policy_valid:
            await encounter_repo.record_verification_event(
                encounter_id, "program_policy", "failed", "POLICY_REJECTED", {"reasons": policy_reasons}
            )
            await encounter_repo.update({"id": f"eq.{encounter_id}"}, {"status": "rejected"})
            return {
                "encounter_id": encounter_id,
                "status": "rejected",
                "stages": ["identity_device", "patient_consent"],
                "reasons": policy_reasons,
                "message": f"Funding policy rejected this claim: {'; '.join(policy_reasons)}"
            }

        await encounter_repo.record_verification_event(encounter_id, "program_policy", "passed", "PROGRAM_POLICY_VALID")

        # STAGE 4: Explainable Anomaly Detection
        risk = await anomaly_detector.assess(encounter, recent_claims, clinic)
        await encounter_repo.record_anomaly_assessment(encounter_id, risk)

        if risk["recommended_action"] == "reject":
            await encounter_repo.record_verification_event(encounter_id, "anomaly_detection", "failed", "CRITICAL_ANOMALY", risk)
            await encounter_repo.update({"id": f"eq.{encounter_id}"}, {"status": "rejected"})
            return {
                "encounter_id": encounter_id,
                "status": "rejected",
                "stages": ["identity_device", "patient_consent", "program_policy", "anomaly_detection"],
                "risk_score": risk["risk_score"],
                "message": "Claim rejected by anomaly detection rules"
            }

        if risk["recommended_action"] == "manual_audit":
            await encounter_repo.record_verification_event(encounter_id, "anomaly_detection", "flagged", "MANUAL_REVIEW_REQUIRED", risk)
            await encounter_repo.update({"id": f"eq.{encounter_id}"}, {"status": "manual_audit"})
            return {
                "encounter_id": encounter_id,
                "status": "manual_audit",
                "stages": ["identity_device", "patient_consent", "program_policy", "anomaly_detection"],
                "risk_score": risk["risk_score"],
                "message": "Claim routed to manual audit; no payout initiated"
            }

        # Passed all 4 stages
        await encounter_repo.record_verification_event(encounter_id, "anomaly_detection", "passed", "ANOMALY_SCORE_ACCEPTABLE", risk)
        return {
            "encounter_id": encounter_id,
            "status": "approved_for_authorization",
            "stages": ["identity_device", "patient_consent", "program_policy", "anomaly_detection"],
            "risk_score": risk["risk_score"],
            "message": "All 4 verification stages passed; ready for atomic funding authorization"
        }


verification_service = VerificationService()
