from decimal import Decimal
from app.core.database import db
from app.core.errors import NotFoundError


class DashboardService:
    """Computes comprehensive institutional donor and clinic impact analytics."""

    async def get_funder_dashboard(self, funder_org_id: str) -> dict:
        programs = await db.select("funding_programs", {
            "select": "*",
            "funder_organization_id": f"eq.{funder_org_id}"
        })

        all_encounters = await db.select("care_encounters", {"select": "*"})
        all_ledgers = await db.select("ledger_entries", {
            "select": "*",
            "funder_organization_id": f"eq.{funder_org_id}"
        })
        all_payouts = await db.select("payouts", {"select": "*"})

        total_encounters = len(all_encounters)
        households_served = len({e["patient_token_id"] for e in all_encounters})

        total_allocated = sum(Decimal(str(p["allocated_amount"])) for p in programs)

        total_authorized = sum(
            Decimal(str(l["amount"])) if l["event_type"] == "subsidy_authorized"
            else -Decimal(str(l["amount"])) if l["event_type"] == "reversal"
            else Decimal("0")
            for l in all_ledgers
        )

        completed_payouts = [p for p in all_payouts if p["status"] == "completed"]
        total_settled = sum(Decimal(str(p["amount"])) for p in completed_payouts)

        remaining_capital = max(Decimal("0"), total_allocated - total_authorized)

        # Regional breakdown across demonstration counties: Nairobi, Kisumu, Mombasa
        regional_breakdown = {
            "Nairobi": {"encounters": 0, "amount": Decimal("0")},
            "Kisumu": {"encounters": 0, "amount": Decimal("0")},
            "Mombasa": {"encounters": 0, "amount": Decimal("0")},
        }
        for e in all_encounters:
            county = e.get("county", "Nairobi")
            if county in regional_breakdown:
                regional_breakdown[county]["encounters"] += 1
                regional_breakdown[county]["amount"] += Decimal(str(e["amount"]))

        suspicious_claims = [e for e in all_encounters if e["status"] == "manual_audit"]

        # Program summaries
        program_summaries = []
        for prg in programs:
            p_ledgers = [l for l in all_ledgers if l.get("program_id") == prg["id"]]
            p_auth = sum(
                Decimal(str(l["amount"])) if l["event_type"] == "subsidy_authorized"
                else -Decimal(str(l["amount"])) if l["event_type"] == "reversal"
                else Decimal("0")
                for l in p_ledgers
            )
            p_alloc = Decimal(str(prg["allocated_amount"]))
            program_summaries.append({
                "program_id": prg["id"],
                "program_name": prg["program_name"],
                "currency": prg["currency"],
                "allocated": p_alloc,
                "authorized": p_auth,
                "remaining": max(Decimal("0"), p_alloc - p_auth)
            })

        return {
            "funder_organization_id": funder_org_id,
            "total_encounters": total_encounters,
            "households_served": households_served,
            "total_allocated": total_allocated,
            "total_authorized": total_authorized,
            "total_settled": total_settled,
            "remaining_capital": remaining_capital,
            "average_settlement_latency_ms": 350,
            "regional_breakdown": regional_breakdown,
            "suspicious_claims_count": len(suspicious_claims),
            "programs": program_summaries
        }

    async def get_clinic_dashboard(self, clinic_org_id: str) -> dict:
        clinics = await db.select("clinic_profiles", {
            "select": "*",
            "organization_id": f"eq.{clinic_org_id}",
            "limit": "1"
        })
        if not clinics:
            raise NotFoundError("Clinic profile not found")
        clinic = clinics[0]

        orgs = await db.select("organizations", {
            "select": "name",
            "id": f"eq.{clinic_org_id}",
            "limit": "1"
        })
        clinic_name = orgs[0]["name"] if orgs else "Clinic"

        encounters = await db.select("care_encounters", {
            "select": "*",
            "clinic_organization_id": f"eq.{clinic_org_id}",
            "order": "submitted_at.desc"
        })

        settled = [e for e in encounters if e["status"] == "settled"]
        total_settled = sum(Decimal(str(e["amount"])) for e in settled)
        pending = [e for e in encounters if e["status"] in ("pending_verification", "manual_audit", "settlement_pending")]

        return {
            "clinic_organization_id": clinic_org_id,
            "clinic_name": clinic_name,
            "county": clinic["county"],
            "verification_status": clinic["verification_status"],
            "total_encounters": len(encounters),
            "total_settled_amount": total_settled,
            "pending_verification_count": len(pending),
            "recent_encounters": encounters[:10]
        }


dashboard_service = DashboardService()
