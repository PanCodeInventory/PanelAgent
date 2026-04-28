"""Admin auth endpoint tests — login, logout, session check, TTL boundary."""

import time

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.app.main import app

TEST_PASSWORD = "test-secret-password-123"
SESSION_SECRET = "test-session-secret-for-tests-only"


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", TEST_PASSWORD)
    monkeypatch.setenv("ADMIN_SESSION_SECRET", SESSION_SECRET)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _login(client: AsyncClient, password: str = TEST_PASSWORD):
    return await client.post("/api/v1/admin/auth/login", json={"password": password})


class TestLogin:
    @pytest.mark.asyncio
    async def test_correct_password_returns_success(self, client):
        resp = await _login(client)
        assert resp.status_code == 200
        assert resp.json() == {"success": True}

    @pytest.mark.asyncio
    async def test_correct_password_sets_session_cookie(self, client):
        resp = await _login(client)
        cookies = {c.name: c for c in resp.cookies.jar}
        assert "panelagent_admin_session" in cookies

    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(self, client):
        resp = await _login(client, password="wrong")
        assert resp.status_code == 401
        assert "panelagent_admin_session" not in {
            c.name for c in resp.cookies.jar
        }

    @pytest.mark.asyncio
    async def test_wrong_password_does_not_set_cookie(self, client):
        resp = await _login(client, password="wrong")
        assert "panelagent_admin_session" not in resp.cookies


class TestSessionCheck:
    @pytest.mark.asyncio
    async def test_unauthenticated_returns_false(self, client):
        resp = await client.get("/api/v1/admin/auth/session")
        assert resp.status_code == 200
        assert resp.json() == {"authenticated": False}

    @pytest.mark.asyncio
    async def test_authenticated_returns_true(self, client):
        login_resp = await _login(client)
        session_cookie = login_resp.cookies.get("panelagent_admin_session")
        resp = await client.get(
            "/api/v1/admin/auth/session",
            cookies={"panelagent_admin_session": session_cookie},
        )
        assert resp.status_code == 200
        assert resp.json() == {"authenticated": True}


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_clears_session(self, client):
        login_resp = await _login(client)
        session_cookie = login_resp.cookies.get("panelagent_admin_session")
        resp = await client.post(
            "/api/v1/admin/auth/logout",
            cookies={"panelagent_admin_session": session_cookie},
        )
        assert resp.status_code == 200
        assert resp.json() == {"success": True}

    @pytest.mark.asyncio
    async def test_after_logout_session_reports_unauthenticated(self, client):
        login_resp = await _login(client)
        session_cookie = login_resp.cookies.get("panelagent_admin_session")
        await client.post(
            "/api/v1/admin/auth/logout",
            cookies={"panelagent_admin_session": session_cookie},
        )
        resp = await client.get("/api/v1/admin/auth/session")
        assert resp.json() == {"authenticated": False}

    @pytest.mark.asyncio
    async def test_logout_without_auth_returns_401(self, client):
        resp = await client.post("/api/v1/admin/auth/logout")
        assert resp.status_code == 401


class TestUnauthenticatedAccess:
    @pytest.mark.asyncio
    async def test_protected_endpoint_returns_401(self, client):
        resp = await client.post("/api/v1/admin/auth/logout")
        assert resp.status_code == 401


class TestSessionTTL:
    @pytest.mark.asyncio
    async def test_expired_session_returns_401(self, client, monkeypatch):
        import backend.app.api.v1.admin.dependencies as dep_mod

        monkeypatch.setattr(dep_mod, "SESSION_TTL_SECONDS", 0)

        login_resp = await _login(client)
        session_cookie = login_resp.cookies.get("panelagent_admin_session")

        time.sleep(0.1)

        resp = await client.post(
            "/api/v1/admin/auth/logout",
            cookies={"panelagent_admin_session": session_cookie},
        )
        assert resp.status_code == 401


class TestPasswordNotConfigured:
    @pytest.mark.asyncio
    async def test_login_fails_when_password_not_set(self, client, monkeypatch):
        monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
        resp = await _login(client)
        assert resp.status_code == 500
