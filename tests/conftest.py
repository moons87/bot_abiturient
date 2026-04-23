import pytest
import os
from knowledge.db import init_db

TEST_DB = "test_database.db"

@pytest.fixture(autouse=True)
async def test_db(monkeypatch):
    monkeypatch.setattr("knowledge.db.DB_PATH", TEST_DB)
    await init_db()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
