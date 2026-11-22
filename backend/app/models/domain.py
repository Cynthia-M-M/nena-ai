from enum import Enum


class OrganizationType(str, Enum):
    CLINIC = "clinic"
    NGO = "ngo"
    GOVERNMENT = "government"
    PLATFORM = "platform"


class OrganizationStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class MembershipRole(str, Enum):
    PLATFORM_ADMIN = "platform_admin"
    CLINIC_ADMIN = "clinic_admin"
    CLINIC_STAFF = "clinic_staff"
    FUNDER_ADMIN = "funder_admin"
    FUNDER_ANALYST = "funder_analyst"
    AUDITOR = "auditor"


class EncounterStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_VERIFICATION = "pending_verification"
    APPROVED = "approved"
    MANUAL_AUDIT = "manual_audit"
    REJECTED = "rejected"
    SETTLEMENT_PENDING = "settlement_pending"
    SETTLED = "settled"


class VerificationStage(str, Enum):
    IDENTITY_DEVICE = "identity_device"
    PATIENT_CONSENT = "patient_consent"
    PROGRAM_POLICY = "program_policy"
    ANOMALY_DETECTION = "anomaly_detection"


class VerificationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    FLAGGED = "flagged"


class LedgerEventType(str, Enum):
    SUBSIDY_AUTHORIZED = "subsidy_authorized"
    SETTLEMENT_CONFIRMED = "settlement_confirmed"
    SETTLEMENT_FAILED = "settlement_failed"
    REVERSAL = "reversal"
    ADJUSTMENT = "adjustment"


class PayoutStatus(str, Enum):
    INITIATED = "initiated"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class TreatmentCode(str, Enum):
    MATERNAL_CARE = "MATERNAL_CARE"
    PEDIATRIC_EMERGENCY = "PEDIATRIC_EMERGENCY"
    MALARIA_LAB = "MALARIA_LAB"
