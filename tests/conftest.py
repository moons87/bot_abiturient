import pytest
from knowledge.db import init_db

@pytest.fixture(autouse=True)
async def test_db(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("knowledge.db.DB_PATH", db_path)
    await init_db()
    yield
