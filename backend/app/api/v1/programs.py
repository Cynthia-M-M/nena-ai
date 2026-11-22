from fastapi import APIRouter, Depends
from app.core.auth import Principal, get_principal, require_membership
from app.core.database import db
from app.core.errors import NotFoundError
from app.schemas.programs import ProgramRuleUpdate, FundingProgramResponse, ProgramRuleResponse

router = APIRouter(prefix="/programs", tags=["Funding Programs"])


@router.get("")
async def list_programs(principal: Principal = Depends(get_principal)):
    """Lists funding programs accessible to the authenticated clinic or funder user."""
    memberships = await db.select("org_memberships", {
        "select": "organization_id",
        "user_id": f"eq.{principal.user_id}",
        "active": "eq.true",
        "limit": "100"
    })
    org_ids = [x["organization_id"] for x in memberships]
    if not org_ids:
        return []

    funder_rows = await db.select("funding_programs", {
        "select": "*",
        "funder_organization_id": f"in.({','.join(org_ids)})",
        "active": "eq.true"
    })
    enrollment_rows = await db.select("clinic_enrollments", {
        "select": "program_id",
        "clinic_organization_id": f"in.({','.join(org_ids)})",
        "active": "eq.true"
    })
    enrolled_ids = {x["program_id"] for x in enrollment_rows}
    clinic_rows = await db.select("funding_programs", {
        "select": "*",
        "id": f"in.({','.join(enrolled_ids)})",
        "active": "eq.true"
    }) if enrolled_ids else []

    unique_programs = {x["id"]: x for x in funder_rows + clinic_rows}
    results = []
    for prg in unique_programs.values():
        rules = await db.select("program_rules", {
            "select": "*",
            "program_id": f"eq.{prg['id']}",
            "active": "eq.true",
            "order": "version.desc",
            "limit": "1"
        })
        prg_copy = dict(prg)
        prg_copy["active_rules"] = rules[0] if rules else None
        results.append(prg_copy)

    return results


@router.get("/{program_id}", response_model=FundingProgramResponse)
async def get_program(program_id: str, principal: Principal = Depends(get_principal)):
    """Retrieves funding program details and active policy rules."""
    programs = await db.select("funding_programs", {"select": "*", "id": f"eq.{program_id}", "limit": "1"})
    if not programs:
        raise NotFoundError("Funding program not found")
    program = dict(programs[0])

    rules = await db.select("program_rules", {
        "select": "*",
        "program_id": f"eq.{program_id}",
        "active": "eq.true",
        "order": "version.desc",
        "limit": "1"
    })
    program["active_rules"] = rules[0] if rules else None
    return program


@router.put("/{program_id}/rules", response_model=ProgramRuleResponse)
async def update_rules(program_id: str, payload: ProgramRuleUpdate, principal: Principal = Depends(get_principal)):
    """Creates a new active rule version for a funding program, preserving previous rules for audit."""
    programs = await db.select("funding_programs", {"select": "id,funder_organization_id", "id": f"eq.{program_id}", "limit": "1"})
    if not programs:
        raise NotFoundError("Funding program not found")

    await require_membership(principal, programs[0]["funder_organization_id"], ["funder_admin", "platform_admin"])

    versions = await db.select("program_rules", {
        "select": "version",
        "program_id": f"eq.{program_id}",
        "order": "version.desc",
        "limit": "1"
    })
    next_version = (versions[0]["version"] + 1) if versions else 1

    # Archive previous rules
    await db.patch("program_rules", {"program_id": f"eq.{program_id}", "active": "eq.true"}, {"active": False})

    # Insert new active version
    insert_data = {
        "program_id": program_id,
        "version": next_version,
        "active": True,
        **payload.model_dump(mode="json")
    }
    rows = await db.insert("program_rules", insert_data)
    return rows[0]
