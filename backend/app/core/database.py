import asyncio
import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
import httpx
from app.core.config import settings
from app.core.errors import ConflictError, NotFoundError, ServiceError
from app.core.logging import safe_logger


class InMemorySupabaseMock:
    """High-fidelity in-memory PostgREST & RPC simulator for automated testing and offline development."""

    def __init__(self):
        self.tables: dict[str, list[dict]] = {
            "organizations": [],
            "user_profiles": [],
            "org_memberships": [],
            "clinic_profiles": [],
            "funding_programs": [],
            "program_rules": [],
            "clinic_enrollments": [],
            "patient_tokens": [],
            "registered_devices": [],
            "care_encounters": [],
            "consent_challenges": [],
            "verification_events": [],
            "anomaly_assessments": [],
            "ledger_chain_state": [{"id": 1, "last_hash": "0" * 64, "updated_at": datetime.now(timezone.utc).isoformat()}],
            "ledger_entries": [],
            "payouts": [],
        }
        self.lock = asyncio.Lock()
        self.reset_seed_data()

    def reset_seed_data(self):
        """Seeds the in-memory database with synthetic Kenyan demonstration data matching seed.sql."""
        now = datetime.now(timezone.utc).isoformat()
        self.tables["organizations"] = [
            {"id": "10000000-0000-4000-8000-000000000001", "name": "AfyaBridge Foundation", "organization_type": "ngo", "registration_number": "DEMO-NGO-001", "status": "active", "created_at": now, "updated_at": now},
            {"id": "20000000-0000-4000-8000-000000000001", "name": "Mwangaza Community Clinic", "organization_type": "clinic", "registration_number": "DEMO-CLINIC-001", "status": "active", "created_at": now, "updated_at": now},
            {"id": "20000000-0000-4000-8000-000000000002", "name": "Lakeview Family Health Centre", "organization_type": "clinic", "registration_number": "DEMO-CLINIC-002", "status": "active", "created_at": now, "updated_at": now},
        ]
        self.tables["clinic_profiles"] = [
            {"organization_id": "20000000-0000-4000-8000-000000000001", "facility_code": "KE-DEMO-NAI-001", "county": "Nairobi", "sub_county": "Westlands", "physical_address": "Demo Road, Nairobi", "latitude": -1.2676, "longitude": 36.8108, "verification_status": "verified", "created_at": now},
            {"organization_id": "20000000-0000-4000-8000-000000000002", "facility_code": "KE-DEMO-KSM-001", "county": "Kisumu", "sub_county": "Kisumu Central", "physical_address": "Demo Avenue, Kisumu", "latitude": -0.0917, "longitude": 34.7680, "verification_status": "verified", "created_at": now},
        ]
        self.tables["funding_programs"] = [
            {
                "id": "40000000-0000-4000-8000-000000000001",
                "funder_organization_id": "10000000-0000-4000-8000-000000000001",
                "program_name": "Community Essential Care Subsidy",
                "description": "Synthetic demo program for eligible maternal, paediatric and malaria services.",
                "currency": "KES",
                "allocated_amount": 5000000.00,
                "starts_at": "2026-01-01T00:00:00Z",
                "ends_at": "2027-12-31T23:59:59Z",
                "active": True,
                "created_at": now
            }
        ]
        self.tables["program_rules"] = [
            {
                "id": "30000000-0000-4000-8000-000000000001",
                "program_id": "40000000-0000-4000-8000-000000000001",
                "max_amount_per_visit": 5000.00,
                "approved_treatment_codes": ["MATERNAL_CARE", "PEDIATRIC_EMERGENCY", "MALARIA_LAB"],
                "allowed_counties": ["Nairobi", "Kisumu", "Mombasa"],
                "requires_patient_otp": True,
                "max_daily_claims": 250,
                "max_household_claims_per_day": 3,
                "geo_fence_radius_m": None,
                "active": True,
                "version": 1,
                "created_at": now
            }
        ]
        self.tables["clinic_enrollments"] = [
            {"id": "71000000-0000-4000-8000-000000000001", "clinic_organization_id": "20000000-0000-4000-8000-000000000001", "program_id": "40000000-0000-4000-8000-000000000001", "active": True, "approved_at": now, "created_at": now},
            {"id": "71000000-0000-4000-8000-000000000002", "clinic_organization_id": "20000000-0000-4000-8000-000000000002", "program_id": "40000000-0000-4000-8000-000000000001", "active": True, "approved_at": now, "created_at": now},
        ]
        # Dynamically derive patient & device HMACs using the active secret
        from app.core.security import keyed_hash
        self.tables["registered_devices"] = [
            {"id": "50000000-0000-4000-8000-000000000001", "clinic_organization_id": "20000000-0000-4000-8000-000000000001", "device_fingerprint_hash": keyed_hash("DEMO-DEVICE-FINGERPRINT-001", "device-fingerprint"), "device_name": "Mwangaza Demo Tablet", "active": True, "last_seen_at": now, "registered_at": now},
            {"id": "50000000-0000-4000-8000-000000000002", "clinic_organization_id": "20000000-0000-4000-8000-000000000002", "device_fingerprint_hash": keyed_hash("DEMO-DEVICE-FINGERPRINT-002", "device-fingerprint"), "device_name": "Lakeview Demo Tablet", "active": True, "last_seen_at": now, "registered_at": now},
        ]
        self.tables["patient_tokens"] = [
            {"id": "60000000-0000-4000-8000-000000000001", "program_id": "40000000-0000-4000-8000-000000000001", "patient_ref_hash": keyed_hash("DEMO-PATIENT-001", "patient-reference"), "coverage_status": "active", "valid_from": "2026-01-01T00:00:00Z", "valid_until": "2027-12-31T23:59:59Z", "created_at": now},
            {"id": "60000000-0000-4000-8000-000000000002", "program_id": "40000000-0000-4000-8000-000000000001", "patient_ref_hash": keyed_hash("DEMO-PATIENT-002", "patient-reference"), "coverage_status": "active", "valid_from": "2026-01-01T00:00:00Z", "valid_until": "2027-12-31T23:59:59Z", "created_at": now},
            # Expired patient token for testing coverage expiration
            {"id": "60000000-0000-4000-8000-000000000003", "program_id": "40000000-0000-4000-8000-000000000001", "patient_ref_hash": keyed_hash("DEMO-PATIENT-EXPIRED", "patient-reference"), "coverage_status": "expired", "valid_from": "2025-01-01T00:00:00Z", "valid_until": "2025-12-31T23:59:59Z", "created_at": now},
        ]
        self.tables["user_profiles"] = [
            {"id": "00000000-0000-0000-0000-000000000001", "full_name": "Clinic Nurse Jane", "phone_encrypted": None, "account_active": True, "created_at": now},
            {"id": "00000000-0000-0000-0000-000000000002", "full_name": "Funder Analyst John", "phone_encrypted": None, "account_active": True, "created_at": now},
            {"id": "00000000-0000-0000-0000-000000000003", "full_name": "Clinic Admin Alice", "phone_encrypted": None, "account_active": True, "created_at": now},
            {"id": "00000000-0000-0000-0000-000000000004", "full_name": "Auditor Bob", "phone_encrypted": None, "account_active": True, "created_at": now},
            {"id": "00000000-0000-0000-0000-000000000005", "full_name": "Platform Admin Root", "phone_encrypted": None, "account_active": True, "created_at": now},
            {"id": "00000000-0000-0000-0000-000000000006", "full_name": "Clinic B Staff Charlie", "phone_encrypted": None, "account_active": True, "created_at": now},
        ]
        self.tables["org_memberships"] = [
            {"id": "90000000-0000-0000-0000-000000000001", "organization_id": "20000000-0000-4000-8000-000000000001", "user_id": "00000000-0000-0000-0000-000000000001", "role": "clinic_staff", "active": True, "created_at": now},
            {"id": "90000000-0000-0000-0000-000000000002", "organization_id": "10000000-0000-4000-8000-000000000001", "user_id": "00000000-0000-0000-0000-000000000002", "role": "funder_admin", "active": True, "created_at": now},
            {"id": "90000000-0000-0000-0000-000000000003", "organization_id": "20000000-0000-4000-8000-000000000001", "user_id": "00000000-0000-0000-0000-000000000003", "role": "clinic_admin", "active": True, "created_at": now},
            {"id": "90000000-0000-0000-0000-000000000004", "organization_id": "10000000-0000-4000-8000-000000000001", "user_id": "00000000-0000-0000-0000-000000000004", "role": "auditor", "active": True, "created_at": now},
            {"id": "90000000-0000-0000-0000-000000000005", "organization_id": "10000000-0000-4000-8000-000000000001", "user_id": "00000000-0000-0000-0000-000000000005", "role": "platform_admin", "active": True, "created_at": now},
            {"id": "90000000-0000-0000-0000-000000000006", "organization_id": "20000000-0000-4000-8000-000000000002", "user_id": "00000000-0000-0000-0000-000000000006", "role": "clinic_staff", "active": True, "created_at": now},
        ]
        self.tables["care_encounters"] = []
        self.tables["consent_challenges"] = []
        self.tables["verification_events"] = []
        self.tables["anomaly_assessments"] = []
        self.tables["ledger_entries"] = []
        self.tables["payouts"] = []
        self.tables["ledger_chain_state"] = [{"id": 1, "last_hash": "0" * 64, "updated_at": now}]

    def _matches_filter(self, row: dict, k: str, v: str) -> bool:
        if k in {"select", "order", "limit", "offset"}:
            return True
        val = row.get(k)
        if v.startswith("eq."):
            target = v[3:]
            if target == "true":
                return val is True
            if target == "false":
                return val is False
            return str(val) == target
        elif v.startswith("neq."):
            return str(val) != v[4:]
        elif v.startswith("in.("):
            candidates = [x.strip() for x in v[4:-1].split(",") if x.strip()]
            return str(val) in candidates
        return True

    async def select(self, table: str, params: dict) -> list[dict]:
        async with self.lock:
            rows = self.tables.get(table, [])
            filtered = []
            for r in rows:
                match = True
                for k, v in params.items():
                    if not self._matches_filter(r, k, v):
                        match = False
                        break
                if match:
                    filtered.append(dict(r))

            if "order" in params:
                order_expr = params["order"]
                field, *dir_part = order_expr.split(".")
                desc = dir_part and dir_part[0] == "desc"
                filtered.sort(key=lambda x: str(x.get(field, "")), reverse=desc)

            if "limit" in params:
                limit = int(params["limit"])
                filtered = filtered[:limit]

            return filtered

    async def insert(self, table: str, payload: dict | list[dict]) -> list[dict]:
        async with self.lock:
            if table not in self.tables:
                self.tables[table] = []
            items = [payload] if isinstance(payload, dict) else payload
            inserted = []
            now = datetime.now(timezone.utc).isoformat()
            for item in items:
                record = dict(item)
                if "id" not in record:
                    record["id"] = str(uuid.uuid4())
                if "created_at" not in record:
                    record["created_at"] = now
                if table == "care_encounters":
                    # Check unique idempotency constraint
                    for existing in self.tables["care_encounters"]:
                        if existing.get("clinic_organization_id") == record.get("clinic_organization_id") and existing.get("idempotency_key") == record.get("idempotency_key"):
                            raise ConflictError("Encounter may already have been submitted; check the idempotency key")
                if table == "ledger_entries":
                    # Simulate trigger generate_ledger_hash()
                    chain_state = self.tables["ledger_chain_state"][0]
                    prev_hash = chain_state["last_hash"]
                    record["prev_hash"] = prev_hash
                    canonical_payload = json.dumps({
                        "id": record["id"],
                        "encounter_id": record["encounter_id"],
                        "program_id": record["program_id"],
                        "clinic_organization_id": record["clinic_organization_id"],
                        "funder_organization_id": record["funder_organization_id"],
                        "event_type": record["event_type"],
                        "amount": str(record["amount"]),
                        "currency": record["currency"],
                        "prev_hash": record["prev_hash"],
                        "metadata": record.get("metadata", {}),
                        "created_by": record.get("created_by"),
                        "created_at": record["created_at"]
                    }, sort_keys=True)
                    tx_hash = hashlib.sha256(canonical_payload.encode()).hexdigest()
                    record["tx_hash"] = tx_hash
                    chain_state["last_hash"] = tx_hash
                    chain_state["updated_at"] = now

                self.tables[table].append(record)
                inserted.append(dict(record))
            return inserted

    async def patch(self, table: str, params: dict, payload: dict) -> list[dict]:
        async with self.lock:
            rows = self.tables.get(table, [])
            updated = []
            now = datetime.now(timezone.utc).isoformat()
            for r in rows:
                match = True
                for k, v in params.items():
                    if not self._matches_filter(r, k, v):
                        match = False
                        break
                if match:
                    r.update(payload)
                    r["updated_at"] = now
                    updated.append(dict(r))
            return updated

    async def rpc(self, function: str, payload: dict) -> Any:
        async with self.lock:
            if function == "authorize_encounter":
                p_encounter_id = payload.get("p_encounter_id")
                # 1. Look up encounter
                encounters = [e for e in self.tables["care_encounters"] if e["id"] == p_encounter_id]
                if not encounters:
                    raise NotFoundError("Encounter not found")
                encounter = encounters[0]

                # 2. Check if already authorized
                existing_ledgers = [l for l in self.tables["ledger_entries"] if l["encounter_id"] == p_encounter_id and l["event_type"] == "subsidy_authorized"]
                if existing_ledgers:
                    payouts = [p for p in self.tables["payouts"] if p["ledger_entry_id"] == existing_ledgers[0]["id"]]
                    return {
                        "ledger_id": existing_ledgers[0]["id"],
                        "payout_id": payouts[0]["id"] if payouts else None,
                        "already_authorized": True,
                        "tx_hash": existing_ledgers[0]["tx_hash"]
                    }

                # 3. Check status
                if encounter["status"] not in ("pending_verification", "approved"):
                    raise ConflictError(f"Encounter is not eligible for authorization: current status {encounter['status']}")

                # 4. Check program
                programs = [p for p in self.tables["funding_programs"] if p["id"] == encounter["program_id"]]
                if not programs or not programs[0]["active"]:
                    raise ConflictError("Funding program inactive or missing")
                program = programs[0]

                if encounter["currency"] != program["currency"]:
                    raise ConflictError("Currency mismatch")

                # 5. Check all 4 verification stages passed
                events = [ev for ev in self.tables["verification_events"] if ev["encounter_id"] == p_encounter_id and ev["status"] == "passed"]
                passed_stages = {ev["stage"] for ev in events}
                if len(passed_stages) < 4:
                    raise ConflictError(f"All four verification stages must pass (passed {len(passed_stages)} of 4)")

                # 6. Check anomaly recommendation
                assessments = [a for a in self.tables["anomaly_assessments"] if a["encounter_id"] == p_encounter_id]
                if not assessments or assessments[-1]["recommended_action"] != "approve":
                    raise ConflictError("Anomaly assessment does not permit automatic authorization")
                risk = assessments[-1]

                # 7. Check committed capital vs allocated
                committed = sum(
                    Decimal(str(l["amount"])) if l["event_type"] == "subsidy_authorized"
                    else -Decimal(str(l["amount"])) if l["event_type"] == "reversal"
                    else Decimal("0")
                    for l in self.tables["ledger_entries"]
                    if l["program_id"] == encounter["program_id"]
                )
                claim_amount = Decimal(str(encounter["amount"]))
                allocated = Decimal(str(program["allocated_amount"]))
                if committed + claim_amount > allocated:
                    raise ConflictError(f"Insufficient uncommitted program funds: committed {committed} + claim {claim_amount} exceeds allocated {allocated}")

                # 8. Append ledger entry with SHA-256 chain
                now = datetime.now(timezone.utc).isoformat()
                chain_state = self.tables["ledger_chain_state"][0]
                prev_hash = chain_state["last_hash"]
                ledger_id = str(uuid.uuid4())
                canonical_payload = json.dumps({
                    "id": ledger_id,
                    "encounter_id": encounter["id"],
                    "program_id": encounter["program_id"],
                    "clinic_organization_id": encounter["clinic_organization_id"],
                    "funder_organization_id": program["funder_organization_id"],
                    "event_type": "subsidy_authorized",
                    "amount": str(encounter["amount"]),
                    "currency": encounter["currency"],
                    "prev_hash": prev_hash,
                    "metadata": {"authorization_source": "nena-fastapi", "risk_score": risk["risk_score"]},
                    "created_by": None,
                    "created_at": now
                }, sort_keys=True)
                tx_hash = hashlib.sha256(canonical_payload.encode()).hexdigest()
                new_ledger = {
                    "id": ledger_id,
                    "encounter_id": encounter["id"],
                    "program_id": encounter["program_id"],
                    "clinic_organization_id": encounter["clinic_organization_id"],
                    "funder_organization_id": program["funder_organization_id"],
                    "event_type": "subsidy_authorized",
                    "amount": str(encounter["amount"]),
                    "currency": encounter["currency"],
                    "prev_hash": prev_hash,
                    "tx_hash": tx_hash,
                    "metadata": {"authorization_source": "nena-fastapi", "risk_score": risk["risk_score"]},
                    "created_by": None,
                    "created_at": now
                }
                self.tables["ledger_entries"].append(new_ledger)
                chain_state["last_hash"] = tx_hash
                chain_state["updated_at"] = now

                # 9. Insert initiated payout
                payout_id = str(uuid.uuid4())
                new_payout = {
                    "id": payout_id,
                    "ledger_entry_id": ledger_id,
                    "provider": "MPESA_MOCK",
                    "amount": str(encounter["amount"]),
                    "currency": encounter["currency"],
                    "status": "initiated",
                    "provider_transaction_id": None,
                    "provider_response": {},
                    "initiated_at": now,
                    "completed_at": None,
                    "updated_at": now
                }
                self.tables["payouts"].append(new_payout)

                # 10. Update encounter status
                encounter["status"] = "settlement_pending"
                encounter["updated_at"] = now

                return {
                    "ledger_id": ledger_id,
                    "payout_id": payout_id,
                    "already_authorized": False,
                    "tx_hash": tx_hash,
                    "amount": str(encounter["amount"]),
                    "currency": encounter["currency"]
                }

            elif function == "verify_ledger_chain":
                entries = sorted(self.tables["ledger_entries"], key=lambda x: (x["created_at"], x["id"]))
                expected_prev = "0" * 64
                inconsistencies = []
                for entry in entries:
                    if entry["prev_hash"] != expected_prev:
                        inconsistencies.append({
                            "entry_id": entry["id"],
                            "error": "PREV_HASH_MISMATCH",
                            "expected_prev": expected_prev,
                            "found_prev": entry["prev_hash"]
                        })
                    canonical_payload = json.dumps({
                        "id": entry["id"],
                        "encounter_id": entry["encounter_id"],
                        "program_id": entry["program_id"],
                        "clinic_organization_id": entry["clinic_organization_id"],
                        "funder_organization_id": entry["funder_organization_id"],
                        "event_type": entry["event_type"],
                        "amount": str(entry["amount"]),
                        "currency": entry["currency"],
                        "prev_hash": entry["prev_hash"],
                        "metadata": entry.get("metadata", {}),
                        "created_by": entry.get("created_by"),
                        "created_at": entry["created_at"]
                    }, sort_keys=True)
                    computed = hashlib.sha256(canonical_payload.encode()).hexdigest()
                    if entry["tx_hash"] != computed:
                        inconsistencies.append({
                            "entry_id": entry["id"],
                            "error": "TX_HASH_CORRUPTION",
                            "expected_tx": computed,
                            "found_tx": entry["tx_hash"]
                        })
                    expected_prev = entry["tx_hash"]
                return {
                    "verified": len(inconsistencies) == 0,
                    "total_entries": len(entries),
                    "current_head_hash": expected_prev,
                    "inconsistencies": inconsistencies
                }

            elif function == "reverse_ledger_entry":
                p_ledger_id = payload.get("p_ledger_id")
                p_reason = payload.get("p_reason", "Administrative reversal")
                p_actor_id = payload.get("p_actor_id")
                orig = next((l for l in self.tables["ledger_entries"] if l["id"] == p_ledger_id), None)
                if not orig:
                    raise NotFoundError("Original ledger entry not found")
                if orig["event_type"] == "reversal":
                    raise ConflictError("Cannot reverse an existing reversal entry")

                now = datetime.now(timezone.utc).isoformat()
                chain_state = self.tables["ledger_chain_state"][0]
                prev_hash = chain_state["last_hash"]
                rev_id = str(uuid.uuid4())
                canonical_payload = json.dumps({
                    "id": rev_id,
                    "encounter_id": orig["encounter_id"],
                    "program_id": orig["program_id"],
                    "clinic_organization_id": orig["clinic_organization_id"],
                    "funder_organization_id": orig["funder_organization_id"],
                    "event_type": "reversal",
                    "amount": str(orig["amount"]),
                    "currency": orig["currency"],
                    "prev_hash": prev_hash,
                    "metadata": {"reversed_ledger_id": orig["id"], "reason": p_reason, "actor_id": p_actor_id},
                    "created_by": p_actor_id,
                    "created_at": now
                }, sort_keys=True)
                tx_hash = hashlib.sha256(canonical_payload.encode()).hexdigest()
                rev_ledger = {
                    "id": rev_id,
                    "encounter_id": orig["encounter_id"],
                    "program_id": orig["program_id"],
                    "clinic_organization_id": orig["clinic_organization_id"],
                    "funder_organization_id": orig["funder_organization_id"],
                    "event_type": "reversal",
                    "amount": str(orig["amount"]),
                    "currency": orig["currency"],
                    "prev_hash": prev_hash,
                    "tx_hash": tx_hash,
                    "metadata": {"reversed_ledger_id": orig["id"], "reason": p_reason, "actor_id": p_actor_id},
                    "created_by": p_actor_id,
                    "created_at": now
                }
                self.tables["ledger_entries"].append(rev_ledger)
                chain_state["last_hash"] = tx_hash
                chain_state["updated_at"] = now

                return {
                    "reversal_ledger_id": rev_id,
                    "reversed_original_id": orig["id"],
                    "tx_hash": tx_hash,
                    "restored_amount": orig["amount"]
                }
            raise ServiceError(f"RPC function {function} not supported")


class SupabaseDB:
    """Async Supabase PostgREST client with transparent test mock capability."""

    def __init__(self) -> None:
        self.base = settings.supabase_url.rstrip("/")
        self.is_mock = (
            "nena-ai-demo" in self.base
            or "YOUR_PROJECT" in self.base
            or settings.app_env in {"test", "development_mock"}
        )
        self._mock = InMemorySupabaseMock() if self.is_mock else None
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(20.0))

    async def close(self) -> None:
        await self.client.aclose()

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": "application/json",
        }
        if extra:
            headers.update(extra)
        return headers

    async def select(self, table: str, params: dict) -> list[dict]:
        if self.is_mock:
            return await self._mock.select(table, params)
        try:
            response = await self.client.get(
                f"{self.base}/rest/v1/{table.lstrip('/')}",
                params=params,
                headers=self._headers()
            )
        except httpx.HTTPError as exc:
            raise ServiceError(f"Database connection failed: {type(exc).__name__}") from exc
        if response.is_error:
            raise ServiceError(f"Database select failed (HTTP {response.status_code})")
        return response.json() if response.content else []

    async def insert(self, table: str, payload: dict | list[dict], *, returning: str = "representation") -> list[dict]:
        if self.is_mock:
            return await self._mock.insert(table, payload)
        try:
            response = await self.client.post(
                f"{self.base}/rest/v1/{table.lstrip('/')}",
                json=payload,
                headers=self._headers({"Prefer": f"return={returning}"})
            )
        except httpx.HTTPError as exc:
            raise ServiceError(f"Database insert connection failed: {type(exc).__name__}") from exc
        if response.is_error:
            if response.status_code == 409:
                raise ConflictError("Database unique constraint violation")
            raise ServiceError(f"Database insert failed (HTTP {response.status_code})")
        return response.json() if response.content else []

    async def patch(self, table: str, params: dict, payload: dict) -> list[dict]:
        if self.is_mock:
            return await self._mock.patch(table, params, payload)
        try:
            response = await self.client.patch(
                f"{self.base}/rest/v1/{table.lstrip('/')}",
                params=params,
                json=payload,
                headers=self._headers({"Prefer": "return=representation"})
            )
        except httpx.HTTPError as exc:
            raise ServiceError(f"Database patch connection failed: {type(exc).__name__}") from exc
        if response.is_error:
            raise ServiceError(f"Database patch failed (HTTP {response.status_code})")
        return response.json() if response.content else []

    async def rpc(self, function: str, payload: dict) -> Any:
        if self.is_mock:
            return await self._mock.rpc(function, payload)
        try:
            response = await self.client.post(
                f"{self.base}/rest/v1/rpc/{function}",
                json=payload,
                headers=self._headers()
            )
        except httpx.HTTPError as exc:
            raise ServiceError("Database RPC connection failed") from exc
        if response.is_error:
            if response.status_code in (400, 409, 422):
                raise ConflictError("Funding authorization was rejected by a database invariant")
            raise ServiceError(f"Database procedure failed (HTTP {response.status_code})")
        return response.json() if response.content else None


db = SupabaseDB()
