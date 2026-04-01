from unittest.mock import AsyncMock
import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.fixture
def mock_es_client():
    client = AsyncMock()
    return client


@pytest.fixture
async def client(mock_es_client):
    app.state.es_client = mock_es_client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
