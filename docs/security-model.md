# Nena AI — Zero-Trust Security & Data Protection Model

**Status:** Active Security Architecture  
**Classification:** Institutional Health-Finance Infrastructure  
**Author:** Zero-Trust Security Engineer & Principal Architect  

---

## 1. Zero-Trust Security Posture

Nena AI implements a strict Zero-Trust Architecture (ZTA). Every request entering the system is treated as potentially hostile regardless of network perimeter or origin. No clinic tablet, user session, or internal proxy is inherently trusted.

### Core Security Mandates:
1. **Explicit Identity Verification**: Every request requires cryptographically signed Supabase Auth JWTs.
2. **Deterministic RBAC & Tenant Isolation**: Membership in an organization (clinic or funder) is verified server-side on every request. Client-supplied headers or bodies claiming an organization ID are rejected or overridden by server-resolved membership records.
3. **No Financial Self-Approval**: Clinic devices cannot approve claims or trigger direct payouts. Payouts require four verified stages and an atomic database-level authorization procedure.
4. **Defense in Depth**: Supabase PostgreSQL Row-Level Security (RLS) protects tenant data at the database engine level, while FastAPI enforces business and role invariants at the application tier.
5. **Least Privilege Credentials**: Public clients receive only the Supabase `anon` key. The `service_role` key is strictly restricted to trusted server environments and is never exposed to the frontend or browser.

---

## 2. Identity, Role-Based Access Control (RBAC) & Tenant Boundaries

### 2.1 Supported System Roles

| Role | Scope | Permitted Operations | Prohibited Operations |
| :--- | :--- | :--- | :--- |
| `platform_admin` | Global Platform | Cross-tenant monitoring, platform configuration, emergency circuit breaker | Direct encounter submission as a clinic |
| `clinic_admin` | Organization (Clinic) | Manage clinic staff, register/revoke clinic devices, view clinic financial dashboard | Accessing other clinics' records or funder pool management |
| `clinic_staff` | Organization (Clinic) | Submit care encounters, verify patient OTP challenges, view clinic claims | Administering devices, editing clinic profiles, approving audits |
| `funder_admin` | Organization (Funder) | Configure funding programs, update policy rules, view regional impact analytics | Submitting care encounters, editing ledger records |
| `funder_analyst` | Organization (Funder) | View read-only dashboard metrics, regional heatmaps, household impact | Editing policy rules, reviewing audit claims |
| `auditor` | Multi-tenant / Independent | Inspect flagged high-risk claims, review four-stage audit evidence, approve/reject | Modifying funding allocations, executing ledger entries directly |

### 2.2 Cross-Tenant Isolation Enforcement
- **Database Layer**: Every query issued by authenticated clients passes through PostgreSQL RLS policies defined in `002_rls_policies.sql`. Helper functions `is_org_member(target_org)` and `has_org_role(target_org, allowed_roles)` prevent cross-tenant data leakage.
- **Application Layer**: In `app/core/auth.py`, `require_membership()` queries `org_memberships` using the authenticated user's `sub` ID to verify active association with the target clinic or funder organization.

---

## 3. Cryptographic Privacy & Data Minimization

In compliance with the **Kenyan Data Protection Act (2019)** and health data privacy principles:

### 3.1 Pseudonymous Patient Reference Hashing
- **National IDs & PII**: Raw National Identification Numbers, Passport numbers, and phone numbers are **NEVER** stored in plain text in application tables.
- **Keyed HMAC-SHA256**: Patient references are transformed at the trusted backend boundary using HMAC-SHA256 with an isolated secret (`APP_HMAC_SECRET`):
  $$\text{patient\_ref\_hash} = \text{HMAC-SHA256}(K_{\text{app}}, \text{"patient-reference:"} \parallel \text{raw\_ref})$$
- Raw references cannot be reconstructed from the database hash without the server secret.
- Plain SHA-256 is explicitly avoided for low-entropy identifiers (such as national IDs) to protect against rainbow table attacks.

### 3.2 Hardware Device Fingerprinting
- Clinic staff devices (smartphones, tablets) compute a client-side device signature based on hardware and browser characteristics.
- The server does not store the raw fingerprint string. Instead, it computes:
  $$\text{device\_fingerprint\_hash} = \text{HMAC-SHA256}(K_{\text{app}}, \text{"device-fingerprint:"} \parallel \text{raw\_fingerprint})$$
- Constant-time string comparison (`hmac.compare_digest`) prevents timing side-channel attacks during device authentication.

### 3.3 Patient Consent Challenge (OTP)
- **Generation**: Cryptographically secure 6-digit numerical codes generated via `secrets.randbelow(1_000_000)`.
- **HMAC Hashing**: OTP values are immediately hashed with the unique challenge ID before storage:
  $$\text{otp\_hash} = \text{HMAC-SHA256}(K_{\text{app}}, \text{"otp:"} \parallel \text{challenge\_id} \parallel \text{otp})$$
- **Expiry & Rate Limiting**:
  - Time-To-Live (TTL): 300 seconds (5 minutes).
  - Maximum verification attempts: 5 attempts. Exceeding attempts permanently invalidates the challenge.
- **Zero Logging Policy**: Raw OTP values are never written to application logs, persistent files, or monitoring traces. In development mode only, synthetic OTPs are returned in the response for automated testing.

---

## 4. Immutable Ledger & Financial Integrity

### 4.1 Cryptographic Hash Chaining
Financial transactions in `ledger_entries` are chained using SHA-256 hashes. Each new entry references the previous transaction's hash, forming an append-only verifiable chain:
- Trigger `generate_ledger_hash()` serializes writes by acquiring an exclusive row lock on `ledger_chain_state(id=1)`.
- The trigger computes the hash over canonical fields:
  - `id`, `encounter_id`, `program_id`, `clinic_organization_id`, `funder_organization_id`, `event_type`, `amount`, `currency`, `prev_hash`, `metadata`, `created_at`.
- Mutating or deleting ledger records is prevented at the database engine level via trigger `trg_ledger_no_update_delete` which throws an unconditional exception.
- Truncating the ledger is prevented via `trg_ledger_no_truncate`.

### 4.2 Concurrency & Overspending Protection
- The stored procedure `public.authorize_encounter` executes within an atomic transaction.
- It acquires an exclusive lock on the `funding_programs` record:
  ```sql
  SELECT * INTO p FROM funding_programs WHERE id = e.program_id FOR UPDATE;
  ```
- It calculates committed capital:
  $$\text{committed} = \sum_{\text{authorized}} \text{amount} - \sum_{\text{reversals}} \text{amount}$$
- If $\text{committed} + \text{claim\_amount} > \text{allocated\_amount}$, the transaction rolls back immediately with code `23514` (Check Violation / Invariant Failure).

---

## 5. Settlement Simulation & Callback Security

### 5.1 Payment Idempotency
- Every encounter requires a client-generated UUID `idempotency_key`.
- Database uniqueness constraint `UNIQUE (clinic_organization_id, idempotency_key)` guarantees that duplicate submissions (such as network retries or offline replay attacks) do not create duplicate encounters or duplicate ledger authorizations.

### 5.2 Provider Callback Verification
- All simulated M-Pesa Daraja callbacks are authenticated using a shared secret signature header (`X-Mpesa-Signature`).
- The signature is calculated as:
  $$\text{Signature} = \text{HMAC-SHA256}(K_{\text{callback}}, \text{request\_body})$$
- Unsigned or invalid callbacks are rejected with HTTP 401 Unauthorized.
- Payout records are only updated to `completed` upon verified successful callback reception.

---

## 6. Threat Matrix & Countermeasure Summary

| Threat Vector | Potential Impact | Zero-Trust Countermeasure |
| :--- | :--- | :--- |
| **Stolen Clinic Credentials** | Attacker attempts to submit claims remotely | Stage 1 checks device fingerprint hash and clinic verification status |
| **Corrupted Clinic Device** | Device replays past claims | Idempotency key uniqueness and patient daily claim limit checks |
| **Patient Identity Spoofing** | Fake claims submitted without patient knowledge | Stage 2 requires patient OTP verification with max 5 attempts and 5-min TTL |
| **Excessive Billing / Inflation** | Clinic claims amount higher than subsidy limit | Stage 3 validates `amount <= max_amount_per_visit` |
| **Budget Exhaustion Race Condition** | Concurrent claims overspend remaining grant pool | Row lock `FOR UPDATE` on `funding_programs` during atomic authorization |
| **Database Tampering** | Rogue DBA alters past payout amounts | SHA-256 chain links detect broken hashes immediately via ledger verification |
| **Cross-Tenant Spying** | Clinic A inspects Clinic B's encounter logs | Supabase RLS enforces `is_org_member()` on every SELECT query |
| **Offline Sync Exploitation** | Syncing fictitious offline claims | Server re-runs all 4 verification stages upon sync before authorization |
