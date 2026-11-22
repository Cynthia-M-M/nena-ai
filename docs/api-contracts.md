# Nena AI — REST API Contracts & Schema Specifications

**API Version:** `v1` (`/api/v1`)  
**Specification:** OpenAPI 3.1 / JSON Schema  
**Protocols:** HTTPS, Application/JSON, Idempotency-Key Headers  

---

## 1. Authentication & Security Headers

All authenticated endpoints require a valid Supabase Auth JWT bearer token:
```http
Authorization: Bearer <supabase_jwt_token>
```
Mutating operations on encounters support idempotent submission:
```http
Idempotency-Key: <uuidv4>
```

---

## 2. Endpoints Specification

### 2.1 Health & Diagnostics
#### `GET /api/v1/health`
Returns service operational health, database connectivity status, and ledger integrity state.
- **Access**: Public
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "environment": "development",
  "database": "connected",
  "ledger_chain_head": "0000000000000000000000000000000000000000000000000000000000000000",
  "timestamp": "2026-11-22T14:50:00Z"
}
```

---

### 2.2 Care Encounters & Verification
#### `POST /api/v1/encounters`
Submit a point-of-care clinical encounter for subsidy authorization.
- **Access**: `clinic_staff`, `clinic_admin` (authenticated clinic membership required)
- **Request Body**:
```json
{
  "program_id": "40000000-0000-4000-8000-000000000001",
  "patient_ref": "DEMO-PATIENT-001",
  "device_id": "50000000-0000-4000-8000-000000000001",
  "device_fingerprint": "DEMO-DEVICE-FINGERPRINT-001",
  "treatment_code": "MALARIA_LAB",
  "description": "Rapid diagnostic malaria antigen test and consultation",
  "amount": "1200.00",
  "currency": "KES",
  "occurred_at": "2026-11-22T10:00:00+03:00",
  "idempotency_key": "70000000-0000-4000-8000-000000000001",
  "offline_created": false
}
```
- **Response `201 Created`**:
```json
{
  "encounter_id": "80000000-0000-4000-8000-000000000001",
  "status": "pending_verification",
  "consent_required": true,
  "message": "DEMO OTP: 123456"
}
```

#### `POST /api/v1/encounters/{id}/consent`
Confirm patient consent challenge with SMS OTP. Initiates stages 2, 3, 4, atomic reservation, and payout.
- **Access**: `clinic_staff`, `clinic_admin`
- **Request Body**:
```json
{
  "otp": "123456"
}
```
- **Response `200 OK` (Standard Settled Path)**:
```json
{
  "encounter_id": "80000000-0000-4000-8000-000000000001",
  "status": "settled",
  "payout_id": "90000000-0000-4000-8000-000000000001",
  "provider": "MPESA_MOCK",
  "provider_transaction_id": "NENA8F3B91A20D1E",
  "amount": "1200.00",
  "currency": "KES",
  "settlement_mode": "SIMULATED_NOT_REAL_MONEY"
}
```
- **Response `200 OK` (Routed to Manual Audit)**:
```json
{
  "encounter_id": "80000000-0000-4000-8000-000000000001",
  "status": "manual_audit",
  "stages": ["identity_device", "patient_consent", "program_policy", "anomaly_detection"],
  "risk_score": 55,
  "message": "Claim routed to manual audit; no payout initiated"
}
```

#### `GET /api/v1/encounters/{id}`
Retrieve encounter details, verification stage status, and associated payout.
- **Access**: `clinic_staff`, `clinic_admin`, `funder_admin`, `auditor`, `platform_admin`

---

### 2.3 Funding Programs & Rules
#### `GET /api/v1/programs`
List funding programs accessible to the authenticated user.
- **Access**: Authenticated

#### `GET /api/v1/programs/{id}`
Get detailed metrics and active rules for a specific funding program.
- **Access**: `funder_admin`, `funder_analyst`, `auditor`, `platform_admin`

#### `PUT /api/v1/programs/{id}/rules`
Update program rules (creates a new active version and archives previous version).
- **Access**: `funder_admin`, `platform_admin`
- **Request Body**:
```json
{
  "max_amount_per_visit": 5000.00,
  "approved_treatment_codes": ["MATERNAL_CARE", "PEDIATRIC_EMERGENCY", "MALARIA_LAB"],
  "allowed_counties": ["Nairobi", "Kisumu", "Mombasa"],
  "requires_patient_otp": true,
  "max_daily_claims": 200,
  "max_household_claims_per_day": 3
}
```

---

### 2.4 Governance & Manual Audit Workflow
#### `GET /api/v1/audit/encounters`
List encounters currently flagged in `manual_audit` status.
- **Access**: `funder_admin`, `auditor`, `platform_admin`

#### `GET /api/v1/audit/encounters/{id}`
Retrieve the comprehensive audit trace for an encounter including all verification events, anomaly assessment breakdown, and financial ledger events.
- **Access**: `funder_admin`, `auditor`, `clinic_admin`, `platform_admin`

#### `POST /api/v1/audit/encounters/{id}/decision`
Submit auditor approval or rejection for a flagged claim.
- **Access**: `funder_admin`, `auditor`, `platform_admin`
- **Request Body**:
```json
{
  "decision": "approve",
  "reason": "Verified clinical emergency and patient identity by telephone callback"
}
```

---

### 2.5 Immutable Ledger & Cryptographic Verification
#### `GET /api/v1/ledger`
Stream of recent append-only ledger events with transaction hashes and previous hashes.
- **Access**: `funder_admin`, `auditor`, `clinic_admin`, `platform_admin`

#### `POST /api/v1/ledger/verify`
Execute cryptographic chain verification across all ledger entries starting from genesis hash. Detects broken links, tampering, or missing transactions.
- **Access**: `auditor`, `funder_admin`, `platform_admin`
- **Response `200 OK`**:
```json
{
  "verified": true,
  "total_entries": 42,
  "genesis_hash": "0000000000000000000000000000000000000000000000000000000000000000",
  "current_head_hash": "a4f89d31b...",
  "inconsistencies": []
}
```

---

### 2.6 Analytics & Dashboards
#### `GET /api/v1/dashboard/funder/{organization_id}`
Comprehensive institutional donor impact analytics.
- **Access**: `funder_admin`, `funder_analyst`, `auditor`, `platform_admin`
- **Response**:
```json
{
  "funder_organization_id": "10000000-0000-4000-8000-000000000001",
  "total_encounters": 128,
  "households_served": 95,
  "total_allocated": 5000000.00,
  "total_authorized": 245000.00,
  "total_settled": 235000.00,
  "remaining_capital": 4755000.00,
  "average_settlement_latency_ms": 348,
  "regional_breakdown": {
    "Nairobi": {"encounters": 80, "amount": 160000.00},
    "Kisumu": {"encounters": 48, "amount": 85000.00},
    "Mombasa": {"encounters": 0, "amount": 0.00}
  },
  "suspicious_claims_count": 2,
  "programs": [...]
}
```

#### `GET /api/v1/dashboard/clinic/{organization_id}`
Clinic financial performance, claim settlement status, and recent activity.
- **Access**: `clinic_admin`, `clinic_staff`, `platform_admin`

---

### 2.7 Payment Simulation & Reconciliation
#### `POST /api/v1/payouts/{id}/simulate`
Manually trigger or simulate an M-Pesa provider callback (e.g. for testing settlement failure and retry).
- **Access**: `platform_admin`
