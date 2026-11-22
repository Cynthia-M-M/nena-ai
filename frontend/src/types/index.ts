export type Role =
  | 'clinic_staff'
  | 'clinic_admin'
  | 'funder_admin'
  | 'funder_analyst'
  | 'auditor'
  | 'platform_admin';

export interface DemoUser {
  user_id: string;
  name: string;
  email: string;
  role: Role;
  organization_id: string;
  organization_name: string;
  organization_type: 'clinic' | 'ngo' | 'platform';
  facility_code?: string;
  county?: string;
  device_id?: string;
  device_name?: string;
  device_fingerprint?: string;
}

export type TreatmentCode = 'MATERNAL_CARE' | 'PEDIATRIC_EMERGENCY' | 'MALARIA_LAB';

export interface EncounterCreate {
  program_id: string;
  patient_ref: string;
  device_id: string;
  device_fingerprint: string;
  treatment_code: TreatmentCode;
  description?: string;
  amount: number | string;
  currency: 'KES' | 'USD';
  occurred_at: string;
  idempotency_key: string;
  offline_created: boolean;
}

export interface EncounterResponse {
  encounter_id: string;
  status: string;
  consent_required: boolean;
  message: string;
}

export interface VerificationEvent {
  id: string;
  encounter_id: string;
  stage: 'identity_device' | 'patient_consent' | 'program_policy' | 'anomaly_detection';
  status: 'passed' | 'failed' | 'flagged';
  reason_code?: string;
  details: Record<string, any>;
  verified_by: string;
  created_at: string;
}

export interface AnomalyAssessment {
  id: string;
  encounter_id: string;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  flags: Array<{ code: string; weight?: number; description?: string; reason?: string }>;
  recommended_action: 'approve' | 'manual_audit' | 'reject';
  created_at: string;
}

export interface LedgerEntry {
  id: string;
  encounter_id: string;
  program_id: string;
  clinic_organization_id: string;
  funder_organization_id: string;
  event_type: 'subsidy_authorized' | 'settlement_confirmed' | 'settlement_failed' | 'reversal' | 'adjustment';
  amount: number | string;
  currency: string;
  prev_hash: string;
  tx_hash: string;
  metadata: Record<string, any>;
  created_by?: string;
  created_at: string;
}

export interface PayoutRecord {
  id: string;
  ledger_entry_id: string;
  provider: string;
  provider_transaction_id?: string;
  amount: number | string;
  currency: string;
  status: 'initiated' | 'processing' | 'completed' | 'failed' | 'reversed';
  initiated_at: string;
  completed_at?: string;
}

export interface EncounterDetail {
  id: string;
  clinic_organization_id: string;
  program_id: string;
  patient_token_id: string;
  submitted_by: string;
  device_id: string;
  treatment_code: string;
  description?: string;
  amount: number | string;
  currency: string;
  county: string;
  occurred_at: string;
  submitted_at: string;
  status: 'pending_verification' | 'manual_audit' | 'approved' | 'rejected' | 'settlement_pending' | 'settled';
  idempotency_key: string;
  offline_created: boolean;
  created_at: string;
}

export interface ProgramRule {
  id: string;
  program_id: string;
  max_amount_per_visit: number | string;
  approved_treatment_codes: string[];
  allowed_counties: string[];
  requires_patient_otp: boolean;
  max_daily_claims: number;
  max_household_claims_per_day: number;
  active: boolean;
  version: number;
}

export interface FundingProgram {
  id: string;
  funder_organization_id: string;
  program_name: string;
  description?: string;
  currency: string;
  allocated_amount: number | string;
  starts_at: string;
  ends_at?: string;
  active: boolean;
  created_at: string;
  active_rules?: ProgramRule;
}

export interface RegionalMetric {
  encounters: number;
  amount: number;
}

export interface FunderDashboardData {
  funder_organization_id: string;
  total_encounters: number;
  households_served: number;
  total_allocated: number;
  total_authorized: number;
  total_settled: number;
  remaining_capital: number;
  average_settlement_latency_ms: number;
  regional_breakdown: Record<string, RegionalMetric>;
  suspicious_claims_count: number;
  programs: Array<{
    program_id: string;
    program_name: string;
    currency: string;
    allocated: number;
    authorized: number;
    remaining: number;
  }>;
}

export interface ClinicDashboardData {
  clinic_organization_id: string;
  clinic_name: string;
  county: string;
  verification_status: string;
  total_encounters: number;
  total_settled_amount: number;
  pending_verification_count: number;
  recent_encounters: EncounterDetail[];
}

export interface AuditDecision {
  decision: 'approve' | 'reject';
  reason: string;
}

export interface AuditDetailResponse {
  encounter: EncounterDetail;
  verification_events: VerificationEvent[];
  risk_assessments: AnomalyAssessment[];
  ledger: LedgerEntry[];
  payouts: PayoutRecord[];
}

export interface LedgerChainVerifyResponse {
  verified: boolean;
  total_entries: number;
  current_head_hash: string;
  inconsistencies: any[];
}

export interface OfflineQueueItem {
  id: string;
  payload: EncounterCreate;
  created_at: string;
  status: 'pending' | 'syncing' | 'synced' | 'failed';
  error?: string;
}
