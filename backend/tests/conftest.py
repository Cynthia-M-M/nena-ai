import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import db
from app.core.security import create_mock_jwt


@pytest.fixture(autouse=True)
def reset_database_state():
    """Resets mock database state before each test run for full isolation."""
    if db.is_mock and db._mock:
        db._mock.reset_seed_data()
    yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def clinic_staff_headers():
    token = create_mock_jwt(user_id="00000000-0000-0000-0000-000000000001", email="jane@mwangazaclinic.ke")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def clinic_b_headers():
    token = create_mock_jwt(user_id="00000000-0000-0000-0000-000000000006", email="charlie@lakeviewclinic.ke")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def funder_headers():
    token = create_mock_jwt(user_id="00000000-0000-0000-0000-000000000002", email="john@afyabridge.org")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auditor_headers():
    token = create_mock_jwt(user_id="00000000-0000-0000-0000-000000000004", email="bob@auditor.ke")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def platform_admin_headers():
    token = create_mock_jwt(user_id="00000000-0000-0000-0000-000000000005", email="root@nena.health")
    return {"Authorization": f"Bearer {token}"}
