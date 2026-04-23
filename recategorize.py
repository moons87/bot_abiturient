"""Перекатегоризация записей в базе знаний без повторного парсинга сайта."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
import aiosqlite
from scraper.site_parser import categorize_section
from knowledge.db import DB_PATH

async def recategorize():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, content FROM knowledge_base") as c:
            rows = await c.fetchall()

        updated = 0
        for row in rows:
            new_section = categorize_section(row["content"])
            await db.execute(
                "UPDATE knowledge_base SET section = ? WHERE id = ?",
                (new_section, row["id"])
            )
            updated += 1

        await db.commit()

        async with db.execute(
            "SELECT section, COUNT(*) as cnt FROM knowledge_base GROUP BY section"
        ) as c:
            stats = await c.fetchall()

    print(f"Перекатегоризировано {updated} записей:")
    for s in stats:
        print(f"  {s['section']}: {s['cnt']}")

asyncio.run(recategorize())
