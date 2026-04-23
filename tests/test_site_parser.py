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
