# Nena AI — Comprehensive Implementation Audit & Technical Analysis

**Date:** November 22, 2026  
**Auditor:** Principal Software Architect & Zero-Trust Security Engineer  
**Project:** Nena AI — Kenyan B2G/B2B Digital Health Financing SaaS  
**Scope:** Phase 1 Foundation, Phase 2 Backend Archive, Business Requirements, Database Reconciliation

---

## 1. Executive Summary & Context

Nena AI connects independent primary healthcare clinics directly with institutional funders (NGOs, donor programs, and government health authorities). Patients access essential medical services at **KES 0 out-of-pocket**, clinics receive prompt, automated settlement via simulated M-Pesa Daraja, and institutional funders obtain real-time, auditable financial and clinical impact metrics through an immutable Zero-Trust Subsidy Routing Ledger.

### Review of Provided Materials:
1. **`nena details/`**:
   - Executive Summary and Investor Pitch Deck (authored by Cynthia Moraa, Lead Software Engineer & Technical Founder).
   - Target metrics: Year 1 pilot with 50 independent clinics scaling to 250 clinics and 250,000 households.
   - Initial intervention treatment categories: `MATERNAL_CARE`, `PEDIATRIC_EMERGENCY`, `MALARIA_LAB`.
   - Brand guidelines: Trust blue (`#0A3D91`), Health-tech teal (`#00C49A`), Slate (`#0F172A`), Canvas (`#F8FAFC`).
2. **`nena-ai-phase1.zip`**:
   - PostgreSQL migrations: `001_initial_schema.sql` (15 tables, append-only trigger), `002_rls_policies.sql` (RLS policies across all tables).
   - Development seed: `seed.sql` with synthetic Kenyan organizations (`AfyaBridge Foundation`, `Mwangaza Community Clinic`, `Lakeview Family Health Centre`), clinics, vouchers, and devices.
   - Foundational documentation: `architecture.md`, `security-model.md`, `folder-structure.md`.
3. **`nena-ai-backend-phase2 (1).zip`**:
   - FastAPI application skeleton (`app/main.py`, `app/core/`, `app/api/v1/`, `app/services/`, `app/integrations/`).
   - Migration `002_atomic_authorization.sql` containing stored procedure `public.authorize_encounter(UUID)`.
   - Basic heuristic anomaly detector and test file `tests/test_anomaly.py`.

---

## 2. In-Depth Component Audit & Gap Analysis

### 2.1 Database Schema vs. Phase 2 Migration Inconsistencies (CRITICAL)

| Component | Phase 1 Schema (`001_initial_schema.sql`) | Phase 2 Implementation (`002_atomic_authorization.sql` & Python) | Severity | Root Cause & Required Fix |
| :--- | :--- | :--- | :--- | :--- |
| **Ledger Event Column** | `event_type public.ledger_event_type NOT NULL` | References `entry_type` in queries and inserts (`002_atomic_authorization.sql` lines 89, 105; `audit.py` line 24; `dashboard.py` line 20) | **BLOCKER** | Column `entry_type` does not exist on `ledger_entries`. The code must use `event_type`. |
| **Ledger Event Enum** | Value is `'subsidy_authorized'` | Uses `'subsidy_authorization'` in SQL procedure and queries | **BLOCKER** | Value `'subsidy_authorization'` violates PostgreSQL enum `ledger_event_type`. Must standardize on `'subsidy_authorized'`. |
| **Ledger Status Column** | `ledger_entries` has NO `status` column (it is an immutable event stream; lifecycle states live on `payouts` and `care_encounters`) | Inserts `'authorized'` into `status` and selects `status` from `ledger_entries` | **BLOCKER** | Attempting to write or query `status` on `ledger_entries` causes `column "status" of relation "ledger_entries" does not exist`. Remove `status` from ledger insert and queries. |
| **Care Encounter `county` Field** | `care_encounters.county text NOT NULL` | `VerificationService.submit` builds `encounter_data` without `county` | **BLOCKER** | Violates NOT NULL constraint when inserting encounter. Must populate `county` from verified `clinic_profiles.county`. |
| **Ledger Hash Trigger Triggering** | `generate_ledger_hash()` computes SHA-256 hash across canonical fields: `id`, `encounter_id`, `program_id`, `clinic_organization_id`, `funder_organization_id`, `event_type`, `amount`, `currency`, `prev_hash`, `metadata`, `created_by`, `created_at` | Function failed because inserted fields mismatched trigger expectations | **HIGH** | Align stored procedure payload with trigger definition so cryptographic chain links without syntax errors. |

---

### 2.2 API Coverage & Endpoint Gap Analysis

| Endpoint Specified in Master Prompt | Existing in Phase 2 Archive | Audit Status | Required Action |
| :--- | :--- | :--- | :--- |
| `GET /api/v1/health` | Yes (`app/api/v1/health.py`) | Basic status check | Enhance with database ping, ledger chain head check, and service status |
| `POST /api/v1/encounters` | Yes (`app/api/v1/encounters.py`) | Incomplete | Fix missing `county`, validate treatment codes, validate device status, enforce rate limits |
| `GET /api/v1/encounters/{id}` | Yes (`app/api/v1/encounters.py`) | Functional | Add role checks and expanded clinical/verification metadata |
| `POST /api/v1/encounters/{id}/consent` | Yes (`app/api/v1/encounters.py`) | Functional | Add OTP rate-limiting, attempt tracking, and failure events |
| `GET /api/v1/programs` | Yes (`app/api/v1/programs.py`) | Functional | Maintain and enrich with active rule summaries |
| `GET /api/v1/programs/{id}` | **Missing** | **MISSING** | Implement program detail lookup with full rule history |
| `PUT /api/v1/programs/{id}/rules` | Yes (`app/api/v1/programs.py`) | Functional | Versioned rule creation working, preserve audit trail |
| `GET /api/v1/audit/encounters` | **Missing** | **MISSING** | Implement listing of claims awaiting manual audit |
| `GET /api/v1/audit/encounters/{id}` | Yes (`app/api/v1/audit.py`) | Broken column names | Fix `entry_type` and `status` queries; return full 4-stage audit trace |
| `POST /api/v1/audit/encounters/{id}/decision` | Yes (`app/api/v1/audit.py`) | Functional | Verify proper transition to atomic authorization upon auditor approval |
| `GET /api/v1/ledger` | **Missing** | **MISSING** | Implement ledger event feed with SHA-256 chain verification utility |
| `GET /api/v1/dashboard/funder/{id}` | Yes (`app/api/v1/dashboard.py`) | Incomplete | Expand to include: total encounters, households served, disbursed capital, average latency, clinic/regional breakdowns (Nairobi, Kisumu, Mombasa), suspicious claims |
| `GET /api/v1/dashboard/clinic/{id}` | **Missing** | **MISSING** | Implement clinic dashboard: total claims, settled amount, pending verification, recent transactions |
| `POST /api/v1/payouts/{id}/simulate` | **Missing** | **MISSING** | Implement manual/webhook simulation endpoint for M-Pesa B2C callback reconciliation |

---

### 2.3 Four-Stage Zero-Trust Verification Engine Audit

1. **Stage 1: Identity & Device Authentication**
   - *Status*: Partially implemented. Clinic verified status and device fingerprint hash checks were present.
   - *Gaps*: Did not check device revocation or enforce user profile active status.
2. **Stage 2: Patient Consent**
   - *Status*: Implemented OTP generation with HMAC hashing.
   - *Gaps*: Lacked explicit sliding-window rate-limiting and mock SMS delivery logging adapter.
3. **Stage 3: Programmatic Policy Validation**
   - *Status*: Checked amount cap, approved treatment code, county, and currency.
   - *Gaps*: Did not check program daily claim limits (`max_daily_claims`) or household daily limits (`max_household_claims_per_day`).
4. **Stage 4: Anomaly Detection**
   - *Status*: Heuristic scoring engine created.
   - *Gaps*: Only checked duplicate, velocity >= 25, amount > 4000, off-hours. Needed clearer threshold controls and explanation breakdowns.

---

### 2.4 Immutable Financial Ledger & Concurrency

- **Chain Integrity**: The Phase 1 trigger `generate_ledger_hash` correctly serializes row locking on `ledger_chain_state(id=1)`. However, the system lacked a chain verification utility in Python to detect chain tampering or orphaned blocks.
- **Race Condition Prevention**: `authorize_encounter` locks `care_encounters` and `funding_programs` using `FOR UPDATE`, ensuring concurrent claims cannot overspend uncommitted allocated program balances.
- **Reversal Handling**: Needed an explicit compensating entry service (`event_type='reversal'`) rather than row mutation.

---

### 2.5 Testing Coverage Audit

- **Existing Tests**: Only 2 tests in `tests/test_anomaly.py`.
- **Required Tests**: Prompt explicitly mandates 12 rigorous integration scenarios (Test 1 through Test 12).
- **Plan**: Implement comprehensive pytest test suites covering all 12 scenarios with a clean test fixture harness that runs in memory/mocked PostgREST client without requiring an external database instance.

---

## 3. Migration and Architecture Plan

1. **Database Reconciliation (`supabase/migrations/003_ledger_and_auth_reconciliation.sql`)**:
   - Fix stored procedure `public.authorize_encounter` to reference `event_type = 'subsidy_authorized'` and remove nonexistent `status` column from `ledger_entries`.
   - Add SQL functions for cryptographic ledger chain verification.
   - Ensure backward compatibility without altering existing tables.
2. **Modular Python Architecture (`backend/app/`)**:
   - `core/`: Config, Security (HMAC, JWT, OTP), Database client (with dual PostgREST / local mock modes for robust test execution), Exceptions.
   - `schemas/`: Complete Pydantic v2 schemas for all entities.
   - `services/`: Verification, Policy Engine, Anomaly Engine, Ledger Service, Settlement Service, Dashboard Service.
   - `integrations/`: Mock M-Pesa Daraja B2C/B2B adapter with callback verification.
   - `api/v1/`: Health, Encounters, Programs, Audit, Dashboard, Ledger, Payouts, Clinics.
3. **Test Suite**:
   - Full implementation of all 12 test scenarios with deterministic assertions.
4. **Docker and Documentation**:
   - Production Dockerfile, docker-compose.yml, architecture, security, and API contract specifications.
