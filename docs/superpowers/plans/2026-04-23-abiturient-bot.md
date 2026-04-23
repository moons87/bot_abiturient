# Telegram-бот для абитуриентов — План реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Собрать Telegram-бот для абитуриентов колледжа с ИИ-ответами на основе данных сайта и документов, профориентационным тестом и системой записи на мероприятия.

**Architecture:** aiogram 3.x обрабатывает входящие сообщения. SQLite хранит базу знаний (контент сайта + документы), FAQ и записи на мероприятия. Свободный текст → поиск по базе знаний → Claude Haiku → ответ. Профтест: 15 вопросов через FSM → Claude → отчёт. Заявки на мероприятия → уведомление администратору в Telegram.

**Tech Stack:** Python 3.11, aiogram==3.13, aiosqlite, anthropic (AsyncAnthropic), beautifulsoup4, requests, PyMuPDF, python-docx, openpyxl, APScheduler, pytest, pytest-asyncio

---

## File Map

| Файл | Ответственность |
|------|----------------|
| `knowledge/db.py` | Все CRUD операции — база знаний, FAQ, мероприятия, заявки |
| `knowledge/search.py` | Поиск по ключевым словам в базе знаний |
| `scraper/site_parser.py` | Парсинг сайта колледжа → чанки базы знаний |
| `scraper/doc_loader.py` | Чтение PDF, Word, Excel из папки `docs/` |
| `ai/claude_client.py` | Обёртка над Claude Haiku API (AsyncAnthropic) |
| `bot/keyboards.py` | Все InlineKeyboardMarkup builders |
| `bot/handlers/menu.py` | /start, главное меню, разделы |
| `bot/handlers/free_text.py` | Свободный текст → поиск + Claude |
| `bot/handlers/faq.py` | Список FAQ и показ ответа |
| `bot/handlers/profitest.py` | Профориентационный тест (FSM, 15 вопросов) |
| `bot/handlers/excursions.py` | Выбор даты и запись на мероприятие (FSM) |
| `bot/handlers/admin.py` | Команды администратора (FSM) |
| `bot/scheduler.py` | Еженедельный автопарсинг сайта |
| `bot/main.py` | Запуск бота, регистрация роутеров |
| `tests/conftest.py` | pytest fixtures (изолированная тестовая БД) |
| `tests/test_db.py` | Тесты CRUD операций |
| `tests/test_search.py` | Тесты поиска по базе знаний |
| `tests/test_site_parser.py` | Тесты парсера сайта (без HTTP) |
| `tests/test_doc_loader.py` | Тесты загрузки документов (temp файлы) |
| `tests/test_claude_client.py` | Тесты Claude клиента (mocked API) |

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `pytest.ini`
- Create: директории `knowledge/`, `scraper/`, `ai/`, `bot/handlers/`, `tests/`, `docs/`

- [ ] **Step 1: Создать структуру директорий**

```bash
mkdir -p knowledge scraper ai bot/handlers tests docs
touch knowledge/__init__.py scraper/__init__.py ai/__init__.py
touch bot/__init__.py bot/handlers/__init__.py tests/__init__.py
```

- [ ] **Step 2: Создать requirements.txt**

```
aiogram==3.13.0
aiosqlite==0.20.0
anthropic==0.40.0
beautifulsoup4==4.12.3
requests==2.32.3
PyMuPDF==1.24.14
python-docx==1.1.2
openpyxl==3.1.5
python-dotenv==1.0.1
APScheduler==3.10.4
pytest==8.3.4
pytest-asyncio==0.24.0
```

- [ ] **Step 3: Создать .env.example**

```
BOT_TOKEN=your_telegram_bot_token
CLAUDE_API_KEY=your_anthropic_api_key
ADMIN_TELEGRAM_ID=your_telegram_user_id
COLLEGE_SITE_URL=https://your-college-site.kz
DB_PATH=database.db
```

- [ ] **Step 4: Создать pytest.ini**

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **Step 5: Установить зависимости**

```bash
pip install -r requirements.txt
```

Expected: все пакеты установлены без ошибок.

- [ ] **Step 6: Commit**

```bash
git init
git add .
git commit -m "feat: project setup"
```

---

### Task 2: Database

**Files:**
- Create: `knowledge/db.py`
- Create: `tests/conftest.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/conftest.py
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
```

```python
# tests/test_db.py
import pytest
from knowledge.db import (
    add_knowledge, get_knowledge_by_section, clear_knowledge_by_source, get_all_knowledge,
    add_faq, get_all_faq, get_faq_by_id, delete_faq,
    add_excursion_date, get_active_excursion_dates, get_excursion_date_by_id,
    delete_excursion_date, register_for_excursion, get_excursion_slots,
    get_excursion_registrations, get_stats,
)

async def test_add_and_get_knowledge():
    await add_knowledge("site", "гранты", "Информация о грантах колледжа")
    rows = await get_knowledge_by_section("гранты")
    assert len(rows) == 1
    assert rows[0]["content"] == "Информация о грантах колледжа"

async def test_clear_knowledge_by_source():
    await add_knowledge("site", "гранты", "Текст 1")
    await add_knowledge("file.pdf", "гранты", "Текст 2")
    await clear_knowledge_by_source("site")
    rows = await get_knowledge_by_section("гранты")
    assert len(rows) == 1
    assert rows[0]["content"] == "Текст 2"

async def test_add_and_get_faq():
    await add_faq("Какие документы нужны?", "Паспорт и аттестат")
    faqs = await get_all_faq()
    assert len(faqs) == 1
    assert faqs[0]["question"] == "Какие документы нужны?"

async def test_get_faq_by_id():
    await add_faq("Вопрос", "Ответ")
    faqs = await get_all_faq()
    faq = await get_faq_by_id(faqs[0]["id"])
    assert faq["answer"] == "Ответ"

async def test_delete_faq():
    await add_faq("Вопрос 1", "Ответ 1")
    faqs = await get_all_faq()
    await delete_faq(faqs[0]["id"])
    assert await get_all_faq() == []

async def test_add_excursion_date():
    await add_excursion_date("2026-05-15", "10:00", "день открытых дверей", 30)
    dates = await get_active_excursion_dates()
    assert len(dates) == 1
    assert dates[0]["max_slots"] == 30
    assert dates[0]["current_slots"] == 0

async def test_register_decrements_slots():
    await add_excursion_date("2026-05-15", "10:00", "экскурсия", 10)
    dates = await get_active_excursion_dates()
    date_id = dates[0]["id"]
    await register_for_excursion(date_id, "Иван Петров", "+77771234567", 123456)
    assert await get_excursion_slots(date_id) == 1

async def test_register_raises_when_full():
    await add_excursion_date("2026-05-16", "11:00", "экскурсия", 1)
    dates = await get_active_excursion_dates()
    date_id = dates[0]["id"]
    await register_for_excursion(date_id, "Иван", "+77771234567", 111)
    with pytest.raises(ValueError, match="no slots"):
        await register_for_excursion(date_id, "Мария", "+77887654321", 222)

async def test_get_stats():
    await add_knowledge("site", "общее", "текст")
    await add_faq("q", "a")
    stats = await get_stats()
    assert stats["knowledge_count"] == 1
    assert stats["faq_count"] == 1
    assert stats["requests_count"] == 0
```

- [ ] **Step 2: Запустить тесты — убедиться что падают**

```bash
pytest tests/test_db.py -v
```

Expected: `ModuleNotFoundError: No module named 'knowledge.db'`

- [ ] **Step 3: Реализовать knowledge/db.py**

```python
# knowledge/db.py
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        async with db.execute(
            "SELECT max_slots, current_slots FROM excursion_dates WHERE id = ?", (date_id,)
        ) as cursor:
            row = await cursor.fetchone()
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
        async with db.execute("SELECT COUNT(*) FROM knowledge_base") as c:
            knowledge_count = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM faq") as c:
            faq_count = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM excursion_requests") as c:
            requests_count = (await c.fetchone())[0]
    return {
        "knowledge_count": knowledge_count,
        "faq_count": faq_count,
        "requests_count": requests_count,
    }
```

- [ ] **Step 4: Запустить тесты — убедиться что проходят**

```bash
pytest tests/test_db.py -v
```

Expected: все тесты PASS

- [ ] **Step 5: Commit**

```bash
git add knowledge/db.py tests/conftest.py tests/test_db.py
git commit -m "feat: database layer with CRUD operations"
```

---

### Task 3: Knowledge Base Search

**Files:**
- Create: `knowledge/search.py`
- Create: `tests/test_search.py`

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/test_search.py
from knowledge.search import find_relevant_chunks
from knowledge.db import add_knowledge

async def test_search_finds_matching_content():
    await add_knowledge("site", "гранты", "Колледж выдаёт гранты отличникам на конкурсной основе")
    await add_knowledge("site", "общежитие", "Общежитие находится по адресу улица Ленина 5")
    results = await find_relevant_chunks("грант для отличников")
    assert len(results) > 0
    assert any("грант" in r.lower() for r in results)

async def test_search_returns_empty_for_no_match():
    await add_knowledge("site", "общее", "Колледж основан в 1990 году")
    results = await find_relevant_chunks("космические корабли")
    assert results == []

async def test_search_case_insensitive():
    await add_knowledge("site", "специальности", "Специальность Информационные системы")
    results = await find_relevant_chunks("ИНФОРМАЦИОННЫЕ системы")
    assert len(results) > 0

async def test_search_returns_max_chunks():
    for i in range(10):
        await add_knowledge("site", "общее", f"грант номер {i} для студентов")
    results = await find_relevant_chunks("грант", max_chunks=3)
    assert len(results) <= 3
```

- [ ] **Step 2: Запустить тесты — убедиться что падают**

```bash
pytest tests/test_search.py -v
```

Expected: `ImportError: cannot import name 'find_relevant_chunks'`

- [ ] **Step 3: Реализовать knowledge/search.py**

```python
# knowledge/search.py
from knowledge.db import get_all_knowledge

async def find_relevant_chunks(query: str, max_chunks: int = 3) -> list[str]:
    keywords = [w.lower() for w in query.split() if len(w) > 2]
    if not keywords:
        return []
    all_knowledge = await get_all_knowledge()
    scored = []
    for row in all_knowledge:
        content_lower = row["content"].lower()
        score = sum(1 for kw in keywords if kw in content_lower)
        if score > 0:
            scored.append((score, row["content"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [content for _, content in scored[:max_chunks]]
```

- [ ] **Step 4: Запустить тесты — убедиться что проходят**

```bash
pytest tests/test_search.py -v
```

Expected: все тесты PASS

- [ ] **Step 5: Commit**

```bash
git add knowledge/search.py tests/test_search.py
git commit -m "feat: keyword search over knowledge base"
```

---

### Task 4: Site Parser

**Files:**
- Create: `scraper/site_parser.py`
- Create: `tests/test_site_parser.py`

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/test_site_parser.py
from scraper.site_parser import categorize_section, extract_text_chunks

def test_categorize_grant():
    assert categorize_section("Грант выдаётся на основе конкурса") == "гранты"

def test_categorize_dormitory():
    assert categorize_section("Общежитие предоставляется иногородним студентам") == "общежитие"

def test_categorize_specialty():
    assert categorize_section("Специальность: Информационные системы") == "специальности"

def test_categorize_other():
    assert categorize_section("Колледж основан в 1990 году") == "общее"

def test_extract_text_chunks():
    html = "<html><body><main><p>Первый абзац с текстом для теста.</p><p>Второй абзац тоже достаточно длинный.</p></main></body></html>"
    chunks = extract_text_chunks(html)
    assert len(chunks) > 0
    assert any("Первый" in c for c in chunks)

def test_extract_ignores_nav():
    html = "<html><body><nav>Навигация сайта меню</nav><main><p>Основной текст страницы колледжа</p></main></body></html>"
    chunks = extract_text_chunks(html)
    assert not any("Навигация" in c for c in chunks)
```

- [ ] **Step 2: Запустить тесты — убедиться что падают**

```bash
pytest tests/test_site_parser.py -v
```

Expected: `ImportError: cannot import name 'categorize_section'`

- [ ] **Step 3: Реализовать scraper/site_parser.py**

```python
# scraper/site_parser.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from knowledge.db import add_knowledge, clear_knowledge_by_source

GRANT_KEYWORDS = ["грант", "стипендия", "финансирование", "льгота", "скидка"]
DORM_KEYWORDS = ["общежитие", "проживание", "комната", "жильё"]
SPEC_KEYWORDS = ["специальность", "направление", "программа", "обучение", "квалификация"]

def categorize_section(text: str) -> str:
    t = text.lower()
    if any(kw in t for kw in GRANT_KEYWORDS):
        return "гранты"
    if any(kw in t for kw in DORM_KEYWORDS):
        return "общежитие"
    if any(kw in t for kw in SPEC_KEYWORDS):
        return "специальности"
    return "общее"

def extract_text_chunks(html: str, min_length: int = 40) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["nav", "footer", "header", "script", "style"]):
        tag.decompose()
    container = soup.find("main") or soup.find("body") or soup
    chunks = []
    for el in container.find_all(["p", "li", "h1", "h2", "h3", "td"]):
        text = el.get_text(" ", strip=True)
        if len(text) >= min_length:
            chunks.append(text)
    return chunks

def get_internal_links(base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    base_domain = urlparse(base_url).netloc
    links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        if urlparse(href).netloc == base_domain:
            links.add(href.split("#")[0])
    return list(links)

async def parse_site(base_url: str, max_pages: int = 50):
    await clear_knowledge_by_source("site")
    visited: set[str] = set()
    to_visit = [base_url]
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (compatible; CollegeBot/1.0)"

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        try:
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
        except Exception:
            continue
        visited.add(url)
        for chunk in extract_text_chunks(resp.text):
            await add_knowledge("site", categorize_section(chunk), chunk)
        for link in get_internal_links(base_url, resp.text):
            if link not in visited:
                to_visit.append(link)
```

- [ ] **Step 4: Запустить тесты — убедиться что проходят**

```bash
pytest tests/test_site_parser.py -v
```

Expected: все тесты PASS

- [ ] **Step 5: Commit**

```bash
git add scraper/site_parser.py tests/test_site_parser.py
git commit -m "feat: college site scraper with content categorization"
```

---

### Task 5: Document Loader

**Files:**
- Create: `scraper/doc_loader.py`
- Create: `tests/test_doc_loader.py`

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/test_doc_loader.py
import os
import tempfile
from scraper.doc_loader import load_docx, load_xlsx, load_all_docs
from knowledge.db import get_all_knowledge

def test_load_docx():
    from docx import Document
    doc = Document()
    doc.add_paragraph("Грант выдаётся студентам с отличным средним баллом от 4.5")
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        doc.save(f.name)
        fname = f.name
    try:
        chunks = load_docx(fname)
        assert len(chunks) > 0
        assert any("Грант" in c for c in chunks)
    finally:
        os.remove(fname)

def test_load_xlsx():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["Специальность", "Код", "Форма обучения"])
    ws.append(["Программирование", "09.02.07", "Очная"])
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        wb.save(f.name)
        fname = f.name
    try:
        chunks = load_xlsx(fname)
        assert any("Программирование" in c for c in chunks)
    finally:
        os.remove(fname)

async def test_load_all_docs_adds_to_db():
    from docx import Document
    doc = Document()
    doc.add_paragraph("Специальность Информационные системы в организации — очная форма")
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "spec.docx")
        doc.save(path)
        await load_all_docs(tmpdir)
    rows = await get_all_knowledge()
    assert len(rows) > 0
```

- [ ] **Step 2: Запустить тесты — убедиться что падают**

```bash
pytest tests/test_doc_loader.py -v
```

Expected: `ImportError: cannot import name 'load_docx'`

- [ ] **Step 3: Реализовать scraper/doc_loader.py**

```python
# scraper/doc_loader.py
import os
import fitz  # PyMuPDF
from docx import Document
from openpyxl import load_workbook
from scraper.site_parser import categorize_section
from knowledge.db import add_knowledge, clear_knowledge_by_source

def load_pdf(path: str, min_length: int = 40) -> list[str]:
    doc = fitz.open(path)
    chunks = []
    for page in doc:
        for line in page.get_text("text").split("\n"):
            line = line.strip()
            if len(line) >= min_length:
                chunks.append(line)
    return chunks

def load_docx(path: str, min_length: int = 30) -> list[str]:
    doc = Document(path)
    return [p.text.strip() for p in doc.paragraphs if len(p.text.strip()) >= min_length]

def load_xlsx(path: str) -> list[str]:
    wb = load_workbook(path, read_only=True)
    chunks = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            cells = [str(c) for c in row if c is not None]
            line = " | ".join(cells)
            if len(line) > 10:
                chunks.append(line)
    return chunks

LOADERS = {".pdf": load_pdf, ".docx": load_docx, ".xlsx": load_xlsx}

async def load_all_docs(docs_dir: str = "docs"):
    for filename in os.listdir(docs_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in LOADERS:
            continue
        path = os.path.join(docs_dir, filename)
        await clear_knowledge_by_source(filename)
        try:
            chunks = LOADERS[ext](path)
        except Exception as e:
            print(f"Не удалось загрузить {filename}: {e}")
            continue
        for chunk in chunks:
            await add_knowledge(filename, categorize_section(chunk), chunk)
```

- [ ] **Step 4: Запустить тесты — убедиться что проходят**

```bash
pytest tests/test_doc_loader.py -v
```

Expected: все тесты PASS

- [ ] **Step 5: Commit**

```bash
git add scraper/doc_loader.py tests/test_doc_loader.py
git commit -m "feat: document loader for PDF, Word, Excel"
```

---

### Task 6: Claude API Client

**Files:**
- Create: `ai/claude_client.py`
- Create: `tests/test_claude_client.py`

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/test_claude_client.py
from unittest.mock import AsyncMock, MagicMock, patch
from ai.claude_client import ask_question, generate_proftest_report

async def test_ask_question_returns_string():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Гранты выдаются на конкурсной основе")]
    with patch("ai.claude_client.client.messages.create", new=AsyncMock(return_value=mock_response)):
        result = await ask_question("Как получить грант?", "Информация о грантах колледжа")
    assert isinstance(result, str)
    assert len(result) > 0

async def test_ask_question_empty_context():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Нет информации по данному вопросу")]
    with patch("ai.claude_client.client.messages.create", new=AsyncMock(return_value=mock_response)):
        result = await ask_question("Неизвестный вопрос", "")
    assert isinstance(result, str)

async def test_generate_proftest_report_returns_string():
    answers = [
        {"question": "Что вам нравится?", "answer": "Работать с данными"},
        {"question": "Какой предмет лучше?", "answer": "Математика"},
    ]
    specialties = ["Информационные системы", "Программирование", "Экономика"]
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Рекомендуем специальность: Программирование")]
    with patch("ai.claude_client.client.messages.create", new=AsyncMock(return_value=mock_response)):
        result = await generate_proftest_report(answers, specialties)
    assert isinstance(result, str)
    assert len(result) > 0
```

- [ ] **Step 2: Запустить тесты — убедиться что падают**

```bash
pytest tests/test_claude_client.py -v
```

Expected: `ImportError: cannot import name 'ask_question'`

- [ ] **Step 3: Реализовать ai/claude_client.py**

```python
# ai/claude_client.py
import os
import anthropic

client = anthropic.AsyncAnthropic(api_key=os.getenv("CLAUDE_API_KEY"))

MODEL = "claude-haiku-4-5-20251001"

async def ask_question(question: str, context: str) -> str:
    if context:
        system = (
            "Ты консультант колледжа. Отвечай на вопросы абитуриентов только на основе "
            "предоставленной информации. Если ответа нет — скажи об этом и предложи "
            "написать администратору.\n\nИнформация о колледже:\n" + context
        )
    else:
        system = (
            "Ты консультант колледжа. По данному вопросу информации нет. "
            "Сообщи об этом и предложи написать администратору."
        )
    response = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    return response.content[0].text

async def generate_proftest_report(answers: list[dict], specialties: list[str]) -> str:
    answers_text = "\n".join(f"- {a['question']}: {a['answer']}" for a in answers)
    specialties_text = "\n".join(f"- {s}" for s in specialties)
    prompt = (
        f"Абитуриент прошёл профориентационный тест. Его ответы:\n{answers_text}\n\n"
        f"Специальности колледжа:\n{specialties_text}\n\n"
        "Напиши развёрнутый отчёт (300-400 слов): проанализируй интересы и сильные стороны, "
        "порекомендуй 2-3 подходящие специальности с объяснением. Пиши дружелюбно."
    )
    response = await client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
```

- [ ] **Step 4: Запустить тесты — убедиться что проходят**

```bash
pytest tests/test_claude_client.py -v
```

Expected: все тесты PASS

- [ ] **Step 5: Commit**

```bash
git add ai/claude_client.py tests/test_claude_client.py
git commit -m "feat: Claude Haiku async client for Q&A and proftest"
```

---

### Task 7: Keyboards

**Files:**
- Create: `bot/keyboards.py`

- [ ] **Step 1: Реализовать bot/keyboards.py**

```python
# bot/keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Специальности", callback_data="section:специальности")],
        [InlineKeyboardButton(text="💰 Гранты", callback_data="section:гранты")],
        [InlineKeyboardButton(text="🏠 Общежитие", callback_data="section:общежитие")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="faq:list")],
        [InlineKeyboardButton(text="📅 Записаться на мероприятие", callback_data="excursion:list")],
        [InlineKeyboardButton(text="🎯 Профориентационный тест", callback_data="proftest:start")],
    ])

def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")]
    ])

def faq_keyboard(faqs: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f["question"][:50], callback_data=f"faq:show:{f['id']}")]
        for f in faqs
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def excursion_dates_keyboard(dates: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for d in dates:
        remaining = d["max_slots"] - d["current_slots"]
        label = f"📅 {d['date']} {d['time']} — {d['type']} (мест: {remaining})"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"excursion:choose:{d['id']}")])
    buttons.append([InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def proftest_answer_keyboard(question_idx: int, options: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{key}) {val}", callback_data=f"pt:{question_idx}:{key}")]
        for key, val in options.items()
    ])

def admin_dates_keyboard(dates: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"❌ {d['date']} {d['time']} — {d['type']}",
            callback_data=f"admin:deldate:{d['id']}",
        )]
        for d in dates
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons or [[]])

def admin_faq_keyboard(faqs: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"❌ {f['question'][:40]}", callback_data=f"admin:delfaq:{f['id']}")]
        for f in faqs
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons or [[]])
```

- [ ] **Step 2: Commit**

```bash
git add bot/keyboards.py
git commit -m "feat: inline keyboards for all bot flows"
```

---

### Task 8: Main Menu and Free Text Handlers

**Files:**
- Create: `bot/handlers/menu.py`
- Create: `bot/handlers/free_text.py`

- [ ] **Step 1: Реализовать bot/handlers/menu.py**

```python
# bot/handlers/menu.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from bot.keyboards import main_menu_keyboard, back_to_menu_keyboard
from knowledge.db import get_knowledge_by_section

router = Router()

WELCOME_TEXT = (
    "Привет! Я бот-помощник для абитуриентов колледжа 🎓\n\n"
    "Помогу узнать о специальностях, грантах, общежитии, "
    "пройти профориентационный тест и записаться на мероприятие.\n\n"
    "Выберите раздел:"
)

@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "menu:main")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_keyboard())

@router.callback_query(F.data.startswith("section:"))
async def section_handler(callback: CallbackQuery):
    section = callback.data.split(":")[1]
    rows = await get_knowledge_by_section(section)
    if not rows:
        text = f"Информация по разделу «{section}» пока не загружена. Напишите нам — ответим!"
    else:
        text = "\n\n".join(r["content"] for r in rows[:5])
        if len(text) > 4000:
            text = text[:4000] + "..."
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard())
```

- [ ] **Step 2: Реализовать bot/handlers/free_text.py**

```python
# bot/handlers/free_text.py
from aiogram import Router
from aiogram.types import Message
from knowledge.search import find_relevant_chunks
from ai.claude_client import ask_question
from bot.keyboards import main_menu_keyboard

router = Router()

@router.message()
async def free_text_handler(message: Message):
    await message.answer("⏳ Ищу ответ...")
    chunks = await find_relevant_chunks(message.text)
    context = "\n\n".join(chunks)
    answer = await ask_question(message.text, context)
    await message.answer(answer, reply_markup=main_menu_keyboard())
```

- [ ] **Step 3: Commit**

```bash
git add bot/handlers/menu.py bot/handlers/free_text.py
git commit -m "feat: main menu and free text handler with Claude"
```

---

### Task 9: FAQ Handler

**Files:**
- Create: `bot/handlers/faq.py`

- [ ] **Step 1: Реализовать bot/handlers/faq.py**

```python
# bot/handlers/faq.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from knowledge.db import get_all_faq, get_faq_by_id
from bot.keyboards import faq_keyboard, back_to_menu_keyboard

router = Router()

@router.callback_query(F.data == "faq:list")
async def faq_list_handler(callback: CallbackQuery):
    faqs = await get_all_faq()
    if not faqs:
        await callback.message.edit_text(
            "Раздел FAQ пока пуст. Задайте вопрос — мы добавим!",
            reply_markup=back_to_menu_keyboard(),
        )
        return
    await callback.message.edit_text(
        "Часто задаваемые вопросы — выберите нужный:",
        reply_markup=faq_keyboard(faqs),
    )

@router.callback_query(F.data.startswith("faq:show:"))
async def faq_show_handler(callback: CallbackQuery):
    faq_id = int(callback.data.split(":")[2])
    faq = await get_faq_by_id(faq_id)
    if not faq:
        await callback.answer("Вопрос не найден", show_alert=True)
        return
    await callback.message.edit_text(
        f"❓ {faq['question']}\n\n✅ {faq['answer']}",
        reply_markup=back_to_menu_keyboard(),
    )
```

- [ ] **Step 2: Commit**

```bash
git add bot/handlers/faq.py
git commit -m "feat: FAQ handler"
```

---

### Task 10: Proforientation Test Handler

**Files:**
- Create: `bot/handlers/profitest.py`

- [ ] **Step 1: Реализовать bot/handlers/profitest.py**

```python
# bot/handlers/profitest.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from ai.claude_client import generate_proftest_report
from bot.keyboards import proftest_answer_keyboard, main_menu_keyboard

router = Router()

COLLEGE_SPECIALTIES = [
    "Информационные системы и программирование",
    "Экономика и бухгалтерский учёт",
    "Строительство и эксплуатация зданий",
    "Сестринское дело",
    "Дошкольное образование",
    "Технология продукции общественного питания",
]

QUESTIONS = [
    {"text": "Что вам больше нравится делать?", "options": {"А": "Работать с цифрами и данными", "Б": "Создавать руками", "В": "Помогать людям и общаться", "Г": "Учиться и исследовать"}},
    {"text": "Какой школьный предмет вам лучше всего даётся?", "options": {"А": "Математика или информатика", "Б": "Труд, черчение", "В": "Биология или химия", "Г": "История, литература"}},
    {"text": "Как вы предпочитаете работать?", "options": {"А": "Один, сосредоточенно", "Б": "Физически, руками", "В": "В команде с людьми", "Г": "Творчески, с новыми идеями"}},
    {"text": "Что вас привлекает в будущей работе?", "options": {"А": "Чёткие задачи и стабильность", "Б": "Помогать другим", "В": "Карьерный рост", "Г": "Творчество и новизна"}},
    {"text": "Как вы решаете сложные задачи?", "options": {"А": "Анализирую данные, строю план", "Б": "Спрашиваю совета", "В": "Пробую разные варианты", "Г": "Доверяю интуиции"}},
    {"text": "Что из этого вы хотели бы изучать?", "options": {"А": "Программирование и IT", "Б": "Медицина и здоровье", "В": "Бизнес и экономика", "Г": "Строительство и архитектура"}},
    {"text": "Где бы вы хотели работать?", "options": {"А": "В офисе, за компьютером", "Б": "В больнице, школе, с людьми", "В": "На производстве или объекте", "Г": "В разных местах, в разъездах"}},
    {"text": "Какое занятие вам ближе всего?", "options": {"А": "Разрабатывать программы или сайты", "Б": "Ухаживать за пациентами", "В": "Вести бизнес и финансы", "Г": "Строить и проектировать"}},
    {"text": "Что важнее для вас в работе?", "options": {"А": "Точность и порядок", "Б": "Живое общение с людьми", "В": "Физическая активность", "Г": "Творческая свобода"}},
    {"text": "Что вас привлекает в технологиях?", "options": {"А": "Программирование и автоматизация", "Б": "Медицинское оборудование", "В": "Строительные технологии", "Г": "Технологии меня не особо интересуют"}},
    {"text": "Как вы относитесь к работе с документами?", "options": {"А": "Нравится, люблю порядок", "Б": "Терплю, предпочитаю общение", "В": "Стараюсь избегать", "Г": "Всё равно"}},
    {"text": "Что вы чаще делаете в интернете?", "options": {"А": "Учусь, читаю статьи", "Б": "Общаюсь, смотрю видео", "В": "Играю в игры", "Г": "Создаю контент"}},
    {"text": "Кем из этих людей вы бы хотели стать?", "options": {"А": "Программист или аналитик", "Б": "Врач или педагог", "В": "Предприниматель или бухгалтер", "Г": "Инженер или строитель"}},
    {"text": "Насколько важна для вас высокая зарплата?", "options": {"А": "Очень важна, это главный критерий", "Б": "Важна, но важнее интерес к работе", "В": "Средне, лишь бы хватало", "Г": "Не главное, важна самореализация"}},
    {"text": "Ваша главная сильная сторона:", "options": {"А": "Аналитическое мышление", "Б": "Эмпатия и коммуникабельность", "В": "Практические навыки, руки", "Г": "Организаторские способности"}},
]

class ProftestStates(StatesGroup):
    answering = State()

@router.callback_query(F.data == "proftest:start")
async def proftest_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProftestStates.answering)
    await state.update_data(current=0, answers=[])
    q = QUESTIONS[0]
    await callback.message.edit_text(
        f"🎯 Профориентационный тест\n\nВопрос 1 из {len(QUESTIONS)}:\n\n{q['text']}",
        reply_markup=proftest_answer_keyboard(0, q["options"]),
    )

@router.callback_query(ProftestStates.answering, F.data.startswith("pt:"))
async def proftest_answer(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    q_idx, chosen_key = int(parts[1]), parts[2]
    data = await state.get_data()
    answers = data["answers"]
    q = QUESTIONS[q_idx]
    answers.append({"question": q["text"], "answer": q["options"][chosen_key]})
    next_idx = q_idx + 1
    if next_idx >= len(QUESTIONS):
        await state.clear()
        await callback.message.edit_text("⏳ Анализирую ваши ответы, подождите 10-20 секунд...")
        report = await generate_proftest_report(answers, COLLEGE_SPECIALTIES)
        await callback.message.edit_text(
            f"🎯 Ваш профориентационный отчёт:\n\n{report}",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await state.update_data(current=next_idx, answers=answers)
        next_q = QUESTIONS[next_idx]
        await callback.message.edit_text(
            f"🎯 Профориентационный тест\n\nВопрос {next_idx + 1} из {len(QUESTIONS)}:\n\n{next_q['text']}",
            reply_markup=proftest_answer_keyboard(next_idx, next_q["options"]),
        )
```

- [ ] **Step 2: Commit**

```bash
git add bot/handlers/profitest.py
git commit -m "feat: 15-question proforientation test with Claude AI report"
```

---

### Task 11: Excursion Registration Handler

**Files:**
- Create: `bot/handlers/excursions.py`

- [ ] **Step 1: Реализовать bot/handlers/excursions.py**

```python
# bot/handlers/excursions.py
import os
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from knowledge.db import (
    get_active_excursion_dates, get_excursion_date_by_id, register_for_excursion,
)
from bot.keyboards import excursion_dates_keyboard, back_to_menu_keyboard

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))

class ExcursionStates(StatesGroup):
    choosing_date = State()
    entering_name = State()
    entering_phone = State()

@router.callback_query(F.data == "excursion:list")
async def excursion_list(callback: CallbackQuery, state: FSMContext):
    dates = await get_active_excursion_dates()
    available = [d for d in dates if d["current_slots"] < d["max_slots"]]
    if not available:
        await callback.message.edit_text(
            "Ближайших мероприятий пока нет. Следите за обновлениями!",
            reply_markup=back_to_menu_keyboard(),
        )
        return
    await state.set_state(ExcursionStates.choosing_date)
    await callback.message.edit_text(
        "Выберите дату мероприятия:",
        reply_markup=excursion_dates_keyboard(available),
    )

@router.callback_query(ExcursionStates.choosing_date, F.data.startswith("excursion:choose:"))
async def excursion_choose_date(callback: CallbackQuery, state: FSMContext):
    date_id = int(callback.data.split(":")[2])
    date_info = await get_excursion_date_by_id(date_id)
    if not date_info:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return
    label = f"{date_info['date']} {date_info['time']} — {date_info['type']}"
    await state.update_data(date_id=date_id, date_label=label)
    await state.set_state(ExcursionStates.entering_name)
    await callback.message.edit_text(f"Вы выбрали: {label}\n\nВведите ваше ФИО:")

@router.message(ExcursionStates.entering_name)
async def excursion_enter_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ExcursionStates.entering_phone)
    await message.answer("Введите ваш номер телефона:")

@router.message(ExcursionStates.entering_phone)
async def excursion_enter_phone(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    try:
        await register_for_excursion(data["date_id"], data["name"], message.text, message.from_user.id)
    except ValueError:
        await message.answer(
            "К сожалению, места на это мероприятие закончились.",
            reply_markup=back_to_menu_keyboard(),
        )
        return
    await message.answer(
        f"✅ Вы успешно записаны!\n\n"
        f"📅 {data['date_label']}\n"
        f"👤 {data['name']}\n"
        f"📞 {message.text}\n\nЖдём вас!",
        reply_markup=back_to_menu_keyboard(),
    )
    if ADMIN_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
        await bot.send_message(
            ADMIN_ID,
            f"📋 Новая заявка на мероприятие!\n\n"
            f"📅 {data['date_label']}\n"
            f"👤 ФИО: {data['name']}\n"
            f"📞 Телефон: {message.text}\n"
            f"🔗 Telegram: {username}",
        )
```

- [ ] **Step 2: Commit**

```bash
git add bot/handlers/excursions.py
git commit -m "feat: excursion registration with admin Telegram notification"
```

---

### Task 12: Admin Commands Handler

**Files:**
- Create: `bot/handlers/admin.py`

- [ ] **Step 1: Реализовать bot/handlers/admin.py**

```python
# bot/handlers/admin.py
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from knowledge.db import (
    add_faq, delete_faq, get_all_faq,
    add_excursion_date, delete_excursion_date, get_active_excursion_dates,
    get_excursion_registrations, get_stats,
)
from bot.keyboards import admin_dates_keyboard, admin_faq_keyboard

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))

def is_admin(message: Message) -> bool:
    return message.from_user.id == ADMIN_ID

class AddFaqStates(StatesGroup):
    question = State()
    answer = State()

class AddDateStates(StatesGroup):
    date = State()
    time = State()
    type_ = State()
    slots = State()

@router.message(Command("stats"))
async def stats_handler(message: Message):
    if not is_admin(message):
        return
    stats = await get_stats()
    await message.answer(
        f"📊 Статистика:\n\n"
        f"📚 Записей в базе знаний: {stats['knowledge_count']}\n"
        f"❓ Вопросов в FAQ: {stats['faq_count']}\n"
        f"📋 Заявок на мероприятия: {stats['requests_count']}"
    )

@router.message(Command("update"))
async def update_handler(message: Message):
    if not is_admin(message):
        return
    url = os.getenv("COLLEGE_SITE_URL")
    if not url:
        await message.answer("COLLEGE_SITE_URL не задан в .env")
        return
    await message.answer("⏳ Начинаю парсинг сайта...")
    from scraper.site_parser import parse_site
    await parse_site(url)
    await message.answer("✅ Сайт загружен в базу знаний!")

@router.message(Command("reload_docs"))
async def reload_docs_handler(message: Message):
    if not is_admin(message):
        return
    await message.answer("⏳ Загружаю документы из папки docs/...")
    from scraper.doc_loader import load_all_docs
    await load_all_docs("docs")
    await message.answer("✅ Документы загружены в базу знаний!")

@router.message(Command("addfaq"))
async def addfaq_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await state.set_state(AddFaqStates.question)
    await message.answer("Введите вопрос для FAQ:")

@router.message(AddFaqStates.question)
async def addfaq_question(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await state.set_state(AddFaqStates.answer)
    await message.answer("Введите ответ:")

@router.message(AddFaqStates.answer)
async def addfaq_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    await add_faq(data["question"], message.text)
    await state.clear()
    await message.answer("✅ Вопрос добавлен в FAQ!")

@router.message(Command("delfaq"))
async def delfaq_handler(message: Message):
    if not is_admin(message):
        return
    faqs = await get_all_faq()
    if not faqs:
        await message.answer("FAQ пуст")
        return
    await message.answer("Выберите вопрос для удаления:", reply_markup=admin_faq_keyboard(faqs))

@router.callback_query(F.data.startswith("admin:delfaq:"))
async def delfaq_confirm(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await delete_faq(int(callback.data.split(":")[2]))
    await callback.message.edit_text("✅ Вопрос удалён из FAQ")

@router.message(Command("adddate"))
async def adddate_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await state.set_state(AddDateStates.date)
    await message.answer("Введите дату (формат ГГГГ-ММ-ДД, например 2026-05-15):")

@router.message(AddDateStates.date)
async def adddate_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.set_state(AddDateStates.time)
    await message.answer("Введите время (формат ЧЧ:ММ, например 10:00):")

@router.message(AddDateStates.time)
async def adddate_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    await state.set_state(AddDateStates.type_)
    await message.answer("Введите тип (например: экскурсия / день открытых дверей):")

@router.message(AddDateStates.type_)
async def adddate_type(message: Message, state: FSMContext):
    await state.update_data(type_=message.text)
    await state.set_state(AddDateStates.slots)
    await message.answer("Введите максимальное количество мест (число):")

@router.message(AddDateStates.slots)
async def adddate_slots(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите число, например: 30")
        return
    data = await state.get_data()
    await add_excursion_date(data["date"], data["time"], data["type_"], int(message.text))
    await state.clear()
    await message.answer(
        f"✅ Мероприятие добавлено!\n"
        f"📅 {data['date']} {data['time']}\n"
        f"📌 {data['type_']}\n"
        f"👥 Мест: {message.text}"
    )

@router.message(Command("deldate"))
async def deldate_handler(message: Message):
    if not is_admin(message):
        return
    dates = await get_active_excursion_dates()
    if not dates:
        await message.answer("Нет активных дат")
        return
    await message.answer("Выберите дату для удаления:", reply_markup=admin_dates_keyboard(dates))

@router.callback_query(F.data.startswith("admin:deldate:"))
async def deldate_confirm(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await delete_excursion_date(int(callback.data.split(":")[2]))
    await callback.message.edit_text("✅ Мероприятие удалено")

@router.message(Command("dates"))
async def dates_handler(message: Message):
    if not is_admin(message):
        return
    dates = await get_active_excursion_dates()
    if not dates:
        await message.answer("Нет активных мероприятий")
        return
    lines = []
    for d in dates:
        regs = await get_excursion_registrations(d["id"])
        lines.append(f"📅 {d['date']} {d['time']} — {d['type']} ({d['current_slots']}/{d['max_slots']})")
        for r in regs:
            lines.append(f"   • {r['name']} {r['phone']}")
    await message.answer("\n".join(lines))
```

- [ ] **Step 2: Commit**

```bash
git add bot/handlers/admin.py
git commit -m "feat: admin commands — dates, FAQ, scraping, stats"
```

---

### Task 13: Scheduler

**Files:**
- Create: `bot/scheduler.py`

- [ ] **Step 1: Реализовать bot/scheduler.py**

```python
# bot/scheduler.py
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def _auto_update():
    url = os.getenv("COLLEGE_SITE_URL")
    if url:
        from scraper.site_parser import parse_site
        await parse_site(url)

def setup_scheduler():
    scheduler.add_job(_auto_update, "cron", day_of_week="mon", hour=3, minute=0)
    scheduler.start()
```

- [ ] **Step 2: Commit**

```bash
git add bot/scheduler.py
git commit -m "feat: weekly auto-scraping scheduler (every Monday 03:00)"
```

---

### Task 14: Bot Main Entry Point

**Files:**
- Create: `bot/main.py`

- [ ] **Step 1: Реализовать bot/main.py**

```python
# bot/main.py
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from knowledge.db import init_db
from bot.handlers import menu, faq, profitest, excursions, admin, free_text
from bot.scheduler import setup_scheduler

async def main():
    await init_db()
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    # Порядок важен: admin и FSM-хендлеры до free_text
    dp.include_router(menu.router)
    dp.include_router(faq.router)
    dp.include_router(profitest.router)
    dp.include_router(excursions.router)
    dp.include_router(admin.router)
    dp.include_router(free_text.router)  # последний — перехватывает всё остальное

    setup_scheduler()
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Создать .env из шаблона и заполнить**

```bash
cp .env.example .env
```

Откройте `.env` и заполните:
- `BOT_TOKEN` — токен от @BotFather
- `CLAUDE_API_KEY` — ключ с console.anthropic.com
- `ADMIN_TELEGRAM_ID` — ваш Telegram user ID (узнать через @userinfobot)
- `COLLEGE_SITE_URL` — URL сайта колледжа

- [ ] **Step 3: Запустить бота**

```bash
python bot/main.py
```

Expected: `Бот запущен...` в консоли. Откройте бота в Telegram, отправьте `/start`.

- [ ] **Step 4: Запустить все тесты**

```bash
pytest tests/ -v
```

Expected: все тесты PASS

- [ ] **Step 5: Commit**

```bash
git add bot/main.py
git commit -m "feat: bot main entry point — all routers wired"
```

---

### Task 15: Initial Data Load and Manual Testing

- [ ] **Step 1: Загрузить данные с сайта**

Отправьте в бот (вы как администратор): `/update`

Expected: бот отвечает "✅ Сайт загружен в базу знаний!"

- [ ] **Step 2: Загрузить документы**

Скопируйте PDF/Word/Excel файлы в папку `docs/`, затем отправьте: `/reload_docs`

Expected: "✅ Документы загружены в базу знаний!"

- [ ] **Step 3: Добавить FAQ**

Отправьте `/addfaq`, введите вопрос и ответ.

- [ ] **Step 4: Добавить дату мероприятия**

Отправьте `/adddate`, пройдите шаги: дата → время → тип → количество мест.

- [ ] **Step 5: Проверить все сценарии**

- [ ] `/start` → показывает главное меню
- [ ] Кнопки "Специальности", "Гранты", "Общежитие" → показывают контент
- [ ] FAQ → список вопросов, нажатие → ответ
- [ ] Свободный текст → ответ от Claude
- [ ] Профтест → 15 вопросов → отчёт от Claude
- [ ] Запись на мероприятие → выбор даты → ФИО → телефон → подтверждение + уведомление администратору
- [ ] `/stats` → статистика
- [ ] `/dates` → список мероприятий с записавшимися

---

### Task 16: Deployment

- [ ] **Step 1: Деплой на Railway**

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

В Railway Dashboard → Variables добавьте:
- `BOT_TOKEN`, `CLAUDE_API_KEY`, `ADMIN_TELEGRAM_ID`, `COLLEGE_SITE_URL`
- `DB_PATH` = `/app/data/database.db`

- [ ] **Step 2: Или деплой на VPS через systemd**

Создайте `/etc/systemd/system/abiturient-bot.service`:

```ini
[Unit]
Description=Abiturient Telegram Bot
After=network.target

[Service]
WorkingDirectory=/home/user/abiturient-bot
ExecStart=/usr/bin/python3 bot/main.py
Restart=always
EnvironmentFile=/home/user/abiturient-bot/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable abiturient-bot
sudo systemctl start abiturient-bot
sudo systemctl status abiturient-bot
```

Expected: `Active: active (running)`

- [ ] **Step 3: Финальный commit**

```bash
git add .
git commit -m "feat: complete abiturient Telegram bot"
```
