# Nena AI — Healthcare Subsidy Routing & Zero-Trust Financial Ledger

**Category:** Kenyan B2G/B2B Digital Health Financing SaaS  
**Founding Team:** Cynthia Moraa (Lead Software Engineer & Technical Founder)  
**Architecture:** Zero-Trust Subsidy Routing Engine, Append-Only SHA-256 Event Ledger, Simulated M-Pesa Daraja Gateway  
**Backend Stack:** Python 3.12 / 3.13, FastAPI, Supabase PostgreSQL, Pydantic v2, Pytest  

---

## 1. Product & Architecture Overview

Nena AI connects independent primary healthcare clinics directly with institutional healthcare funders (NGOs, donor programs, and government health authorities).
- **For Vulnerable Patients:** Instant access to eligible essential clinical interventions (`MATERNAL_CARE`, `PEDIATRIC_EMERGENCY`, `MALARIA_LAB`) at **KES 0 out-of-pocket**.
- **For Independent Clinics:** Guaranteed, automated settlements eliminating manual invoice bottlenecks, with PWA offline-first support.
- **For Institutional Donors (NGOs & B2G):** Complete transparency, real-time clinical impact metrics, and mathematical proof of fund routing via an immutable Zero-Trust Subsidy Routing Ledger.

---

## 2. Technology Stack

- **Backend:** Python 3.12 / 3.13, FastAPI, Supabase PostgREST Client, Pydantic v2, Pytest, Cryptography (HMAC-SHA256, RFC-7519 JWT).
- **Database:** Supabase PostgreSQL, Row-Level Security (RLS), `FOR UPDATE` atomic row-level reservation, append-only trigger, SHA-256 cryptographic chain integrity verification function.
- **Frontend:** React 19, Vite, Tailwind CSS v4, Lucide Icons, Recharts, `idb` (IndexedDB PWA offline queue), TypeScript.
- **Settlement:** Mock M-Pesa Daraja B2C/B2B payment simulation with cryptographic signature verification.
- **Containerization:** Docker & Docker Compose (`nena-ai-backend` and `nena-ai-frontend`).

---

## 2. Four-Stage Zero-Trust Verification Engine

Every claim must pass through all four stages before financial authorization:

```
[Point of Care]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 1: Identity & Device Authentication               │
│ - Verified clinic status check                         │
│ - Hardware attestation & device fingerprint HMAC match │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 2: Patient Consent Challenge                     │
│ - Short-lived 6-digit OTP (5-minute TTL)               │
│ - Keyed HMAC verification & sliding-window rate limit  │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 3: Programmatic Policy Validation                │
│ - Active funding program & clinic enrollment check     │
│ - Patient coverage validity window                     │
│ - Approved treatment codes & geographical counties     │
│ - Maximum billing cap per visit & daily limits         │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 4: Heuristic Anomaly Scoring                     │
│ - Duplicate claim detection (+55 score)                │
│ - High submission velocity & billing spikes            │
│ - Off-hours activity detection                         │
│ - Score >= 40 routed to HUMAN AUDIT; Low-risk approved │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ ATOMIC LEDGER RESERVATION & SETTLEMENT                 │
│ - PostgreSQL FOR UPDATE row locking                    │
│ - Append-only SHA-256 chained transaction              │
│ - Simulated M-Pesa Daraja B2C disbursement             │
└────────────────────────────────────────────────────────┘
```

---

## 3. Repository Directory Structure

```text
nena-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Versioned REST routers (health, encounters, programs, audit, ledger, dashboard, payouts, clinics)
│   │   ├── core/            # Config, security (HMAC/JWT/OTP), database client, errors, logging
│   │   ├── integrations/    # Mock M-Pesa Daraja and mock SMS gateway adapters
│   │   ├── models/          # Domain enums and entity definitions
│   │   ├── repositories/    # Clean PostgREST database abstraction layer
│   │   ├── schemas/         # Pydantic v2 validation contracts
│   │   ├── services/        # Verification, policy, anomaly, ledger, settlement, and dashboard services
│   │   └── main.py          # FastAPI application entry point, CORS, lifespan, exception handlers
│   ├── tests/               # 20 automated tests covering all 12 required test scenarios
│   ├── scripts/             # Seed demo hashes synchronization utility
│   ├── requirements.txt     # Python production dependencies
│   ├── Dockerfile           # Multi-stage production container definition
│   └── pytest.ini           # Pytest async configuration
├── supabase/
│   ├── migrations/
│   │   ├── 001_initial_schema.sql                  # Core tables, append-only trigger, constraints
│   │   ├── 002_rls_policies.sql                    # Tenant-scoped Row-Level Security policies
│   │   └── 003_ledger_and_auth_reconciliation.sql  # Atomic authorization & chain verification procedure
│   ├── seed.sql                                    # Synthetic Kenyan demonstration data
│   └── config.toml                                 # Local Supabase CLI configuration
├── docs/
│   ├── implementation-audit.md                     # Comprehensive gap analysis & audit report
│   ├── architecture.md                             # Architectural blueprint and sequence flows
│   ├── security-model.md                           # Zero-trust security model and threat matrix
│   └── api-contracts.md                            # Complete OpenAPI / REST schema contracts
├── nena details/                                   # Executive summary, pitch deck, logos
├── docker-compose.yml                              # Single-command container deployment
├── .env.example                                    # Environment variable documentation
└── README.md
```

---

## 4. Quick Start: Local Installation & Execution (Windows / macOS / Linux)

### Step 1: Create Virtual Environment
```powershell
# Windows PowerShell:
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 3: Configure Environment
```bash
cp .env.example backend/.env
```
Ensure `APP_HMAC_SECRET` and `MPESA_CALLBACK_SECRET` are set to 64-character random hex strings.

### Step 4: Run Automated Test Suite
To run all 20 tests covering the 12 required architectural scenarios:
```powershell
# PowerShell:
$env:PYTHONPATH="backend"
pytest backend/tests

# Bash / Linux:
PYTHONPATH=backend pytest backend/tests
```

### Step 5: Start the API Server
```powershell
# PowerShell:
$env:PYTHONPATH="backend"
uvicorn app.main:app --app-dir backend --reload --port 8000
```
- Interactive Swagger API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

### Step 6: Start the Frontend Application (Development Mode)
```powershell
# In a new terminal:
cd frontend
npm run dev
```
Open your browser at `http://localhost:5173`.
The frontend proxies `/api` calls directly to the FastAPI backend running on port 8000.

---

## 5. Applying Database Migrations to Supabase

1. Connect to your Supabase project dashboard or local CLI (`supabase start`).
2. Run `supabase/migrations/001_initial_schema.sql` in the Supabase SQL Editor.
3. Run `supabase/migrations/002_rls_policies.sql`.
4. Run `supabase/migrations/003_ledger_and_auth_reconciliation.sql`.
5. (Development only) Apply `supabase/seed.sql` to populate synthetic clinics and vouchers.
6. Synchronize demonstration hashes with your local `APP_HMAC_SECRET`:
   ```bash
   python scripts/seed_demo_hashes.py
   ```

---

## 6. Docker Deployment (Full Stack)

To build and run both the FastAPI backend and React frontend inside Docker:
```bash
docker compose up --build
```
- **React Frontend:** `http://localhost:3000`
- **FastAPI Backend:** `http://localhost:8000`
- **API Swagger Docs:** `http://localhost:8000/docs`
- **Health-Check Endpoint:** `http://localhost:8000/api/v1/health`

Both containers run on an isolated bridge network, with the frontend Nginx reverse proxy routing `/api/` traffic to the backend.

---

## 7. Automated Test Verification Results

All 12 mandatory scenarios pass deterministically:

| Test ID | Scenario | Verification Result |
| :--- | :--- | :--- |
| **TEST 1** | Successful end-to-end transaction | **PASSED** (Encounter submitted -> OTP validated -> Policy passed -> Low risk -> Ledger authorized -> Settled via Mock M-Pesa) |
| **TEST 2** | Duplicate claim protection | **PASSED** (Idempotency key uniqueness prevents duplicate submissions) |
| **TEST 3** | Invalid OTP challenge | **PASSED** (Incorrect OTP rejected; claim cannot proceed to authorization) |
| **TEST 4** | Ineligible patient coverage | **PASSED** (Expired or missing patient coverage rejected) |
| **TEST 5** | Excessive billing cap | **PASSED** (Amount exceeding KES 5,000 cap rejected by policy engine) |
| **TEST 6** | Fraudulent activity & manual audit | **PASSED** (Duplicate service flagged -> routed to `manual_audit` -> reviewed by auditor) |
| **TEST 7** | Insufficient funding | **PASSED** (Claims exceeding remaining program balance rejected) |
| **TEST 8** | Concurrent transaction safety | **PASSED** (Simultaneous claims locked `FOR UPDATE`; overspend prevented) |
| **TEST 9** | Cryptographic ledger tampering | **PASSED** (Altered amounts detect `TX_HASH_CORRUPTION` and broken hash chains) |
| **TEST 10** | Tenant access control | **PASSED** (Clinic A cannot read or verify Clinic B's records) |
| **TEST 11** | Failed settlement reconciliation | **PASSED** (Provider failure retains status `settlement_pending`, no false success) |
| **TEST 12** | Offline synchronization | **PASSED** (Queued offline encounter re-verified server-side before ledger reservation) |

---

## 8. Compliance & Pilot Operational Guardrails

- **Simulation Safeguard:** M-Pesa Daraja integration in this MVP is simulated. No real money moves.
- **SMS Delivery:** In development mode, synthetic OTPs are returned in the response for automated testing. In production, OTPs are dispatched strictly through an approved SMS provider with zero-logging.
- **Data Protection:** National IDs and raw device fingerprints are never stored in plain text. HMAC-SHA256 references with a server secret are strictly enforced.
- **Regulatory Readiness:** Prior to operational pilot deployment in Kenyan clinics, formal review under the **Kenyan Data Protection Act (2019)** and **Digital Health Act (2023)** must be conducted.
