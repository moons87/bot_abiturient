import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "database.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                section TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS excursion_dates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                type TEXT NOT NULL,
                max_slots INTEGER NOT NULL,
                current_slots INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS excursion_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                excursion_date_id INTEGER REFERENCES excursion_dates(id),
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                telegram_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_knowledge(source: str, section: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO knowledge_base (source, section, content) VALUES (?, ?, ?)",
            (source, section, content),
        )
        await db.commit()

async def get_knowledge_by_section(section: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM knowledge_base WHERE section = ?", (section,)
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

async def clear_knowledge_by_source(source: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM knowledge_base WHERE source = ?", (source,))
        await db.commit()

async def get_all_knowledge() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM knowledge_base") as cursor:
            return [dict(r) for r in await cursor.fetchall()]

async def add_faq(question: str, answer: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO faq (question, answer) VALUES (?, ?)", (question, answer)
        )
        await db.commit()

async def get_all_faq() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM faq ORDER BY id") as cursor:
            return [dict(r) for r in await cursor.fetchall()]

async def get_faq_by_id(faq_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM faq WHERE id = ?", (faq_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def delete_faq(faq_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM faq WHERE id = ?", (faq_id,))
        await db.commit()

async def add_excursion_date(date: str, time: str, type_: str, max_slots: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO excursion_dates (date, time, type, max_slots) VALUES (?, ?, ?, ?)",
            (date, time, type_, max_slots),
        )
        await db.commit()

async def get_active_excursion_dates() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM excursion_dates WHERE is_active = 1 ORDER BY date, time"
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

async def get_excursion_date_by_id(date_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM excursion_dates WHERE id = ?", (date_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def delete_excursion_date(date_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE excursion_dates SET is_active = 0 WHERE id = ?", (date_id,)
        )
        await db.commit()

async def register_for_excursion(
    date_id: int, name: str, phone: str, telegram_user_id: int
):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("BEGIN IMMEDIATE")
        async with db.execute(
            "SELECT max_slots, current_slots FROM excursion_dates WHERE id = ?", (date_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            raise ValueError("excursion date not found")
        if row["current_slots"] >= row["max_slots"]:
            raise ValueError("no slots available")
        await db.execute(
            "INSERT INTO excursion_requests (excursion_date_id, name, phone, telegram_user_id) VALUES (?, ?, ?, ?)",
            (date_id, name, phone, telegram_user_id),
        )
        await db.execute(
            "UPDATE excursion_dates SET current_slots = current_slots + 1 WHERE id = ?",
            (date_id,),
        )
        await db.commit()

async def get_excursion_slots(date_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT current_slots FROM excursion_dates WHERE id = ?", (date_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_excursion_registrations(date_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM excursion_requests WHERE excursion_date_id = ?", (date_id,)
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("BEGIN DEFERRED")
        async with db.execute("SELECT COUNT(*) FROM knowledge_base") as c:
            knowledge_count = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM faq") as c:
            faq_count = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM excursion_requests") as c:
            requests_count = (await c.fetchone())[0]
        await db.execute("ROLLBACK")
    return {
        "knowledge_count": knowledge_count,
        "faq_count": faq_count,
        "requests_count": requests_count,
    }
