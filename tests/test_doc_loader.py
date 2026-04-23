# tests/test_doc_loader.py
from scraper.doc_loader import load_docx, load_xlsx, load_all_docs
from knowledge.db import get_all_knowledge

def test_load_docx(tmp_path):
    from docx import Document
    doc = Document()
    doc.add_paragraph("Грант выдаётся студентам с отличным средним баллом от 4.5")
    path = tmp_path / "test.docx"
    doc.save(str(path))
    chunks = load_docx(str(path))
    assert len(chunks) > 0
    assert any("Грант" in c for c in chunks)

def test_load_xlsx(tmp_path):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["Специальность", "Код", "Форма обучения"])
    ws.append(["Программирование", "09.02.07", "Очная"])
    path = tmp_path / "test.xlsx"
    wb.save(str(path))
    chunks = load_xlsx(str(path))
    assert any("Программирование" in c for c in chunks)

async def test_load_all_docs_adds_to_db(tmp_path):
    from docx import Document
    doc = Document()
    doc.add_paragraph("Специальность Информационные системы в организации — очная форма")
    path = tmp_path / "spec.docx"
    doc.save(str(path))
    await load_all_docs(str(tmp_path))
    rows = await get_all_knowledge()
    assert len(rows) > 0
