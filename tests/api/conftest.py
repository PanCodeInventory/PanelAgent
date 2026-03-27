import shutil

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.app.main import app


@pytest.fixture(scope="session", autouse=True)
def ensure_panel_inventory_fixture(project_root, fixtures_dir):
    inventory_dir = project_root / "inventory"
    inventory_dir.mkdir(exist_ok=True)
    shutil.copyfile(fixtures_dir / "panel_inventory.csv", inventory_dir / "panel_inventory.csv")


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
