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
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_characters_empty(client):
    resp = await client.get("/api/v1/characters")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_character(client):
    resp = await client.post("/api/v1/characters", json={
        "name": "Test Hero",
        "race": "Human",
        "char_class": "Fighter",
        "level": 1,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Hero"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_stories(client):
    resp = await client.get("/api/v1/stories")
    assert resp.status_code == 200
    stories = resp.json()
    assert any(s["title"] == "The Lost Mine of Phandelver" for s in stories)


@pytest.mark.asyncio
async def test_get_settings(client):
    resp = await client.get("/api/v1/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "ollama_model" in data
    assert "context_length" in data
