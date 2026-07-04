"""Tests for core-api endpoints."""
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
    assert data["status"] == "ok"
    assert data["service"] == "core-api"


@pytest.mark.asyncio
async def test_list_surahs(client):
    resp = await client.get("/v1/surahs", params={"lang": "en"})
    assert resp.status_code == 200
    surahs = resp.json()
    assert len(surahs) == 114
    assert surahs[0]["surah_number"] == 1


@pytest.mark.asyncio
async def test_get_surah_detail(client):
    resp = await client.get("/v1/surahs/1", params={"lang": "en"})
    assert resp.status_code == 200
    surah = resp.json()
    assert surah["name_translit"] == "Al-Fatihah"


@pytest.mark.asyncio
async def test_invalid_surah(client):
    resp = await client.get("/v1/surahs/999")
    assert resp.status_code == 400
