from dataclasses import dataclass
import httpx
from fastapi import Depends, Header
from jose import JWTError, jwt
from app.core.config import settings
from app.core.database import db
from app.core.errors import DomainError, ForbiddenError


@dataclass(frozen=True)
class Principal:
    user_id: str
    email: str | None
    access_token: str


async def get_principal(authorization: str | None = Header(default=None)) -> Principal:
    """Validates JWT bearer token and resolves the principal user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise DomainError("UNAUTHENTICATED", "Bearer access token required", 401)

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise DomainError("UNAUTHENTICATED", "Bearer access token required", 401)

    # 1. Check local/test JWT verification first if secret configured or mock DB active
    secret = settings.supabase_jwt_secret or settings.app_hmac_secret
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
        user_id = payload.get("sub") or payload.get("id")
        if user_id:
            return Principal(user_id=user_id, email=payload.get("email"), access_token=token)
    except JWTError:
        pass

    # 2. Query Supabase Auth service
    if not db.is_mock:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
                    headers={"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {token}"}
                )
            except httpx.HTTPError as exc:
                raise DomainError("AUTH_UNAVAILABLE", "Authentication service unavailable", 503) from exc

        if response.status_code == 200:
            data = response.json()
            return Principal(user_id=data["id"], email=data.get("email"), access_token=token)

    # 3. In mock mode with synthetic tokens:
    if db.is_mock and token.startswith("test-token-"):
        # Allow test-token-<user_id> in test mode
        user_id = token.replace("test-token-", "")
        return Principal(user_id=user_id, email=f"{user_id}@nena.health", access_token=token)

    raise DomainError("UNAUTHENTICATED", "Invalid or expired access token", 401)


async def require_membership(principal: Principal, organization_id: str, roles: list[str] | None = None) -> dict:
    """Enforces active organization membership and optional role authorization."""
    rows = await db.select("org_memberships", {
        "select": "id,organization_id,user_id,role,active",
        "organization_id": f"eq.{organization_id}",
        "user_id": f"eq.{principal.user_id}",
        "active": "eq.true",
        "limit": "1",
    })

    if not rows:
        # Platform-admin membership authorizes platform operations
        admin = await db.select("org_memberships", {
            "select": "id,organization_id,user_id,role,active",
            "user_id": f"eq.{principal.user_id}",
            "role": "eq.platform_admin",
            "active": "eq.true",
            "limit": "1"
        })
        if admin:
            return admin[0]
        raise ForbiddenError("Active organization membership required")

    membership = rows[0]
    if roles and membership["role"] not in roles and membership["role"] != "platform_admin":
        raise ForbiddenError(f"Role '{membership['role']}' is not authorized to perform this action")

    return membership


async def current_principal(principal: Principal = Depends(get_principal)) -> Principal:
    return principal
