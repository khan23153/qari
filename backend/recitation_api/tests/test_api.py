"""Tests for recitation-api endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "recitation-api"


@pytest.mark.asyncio
async def test_get_result_not_ready(client):
    import uuid
    resp = await client.get(f"/v1/recitations/{uuid.uuid4()}")
    assert resp.status_code == 202
