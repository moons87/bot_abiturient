from knowledge.search import find_relevant_chunks
from knowledge.db import add_knowledge

async def test_search_finds_matching_content():
    await add_knowledge("site", "гранты", "Колледж выдаёт гранты отличникам на конкурсной основе")
    await add_knowledge("site", "общежитие", "Общежитие находится по адресу улица Ленина 5")
    results = await find_relevant_chunks("гранты для отличников")
    assert len(results) > 0
    assert any("гранты" in r.lower() for r in results)

async def test_search_returns_empty_for_no_match():
    await add_knowledge("site", "общее", "Колледж основан в 1990 году")
    results = await find_relevant_chunks("космические корабли")
    assert results == []

async def test_search_case_insensitive():
    await add_knowledge("site", "специальности", "Специальность Информационные системы")
    results = await find_relevant_chunks("информационные системы")
    assert len(results) > 0

async def test_search_returns_max_chunks():
    for i in range(10):
        await add_knowledge("site", "общее", f"грант номер {i} для студентов")
    results = await find_relevant_chunks("грант", max_chunks=3)
    assert len(results) <= 3

async def test_search_no_false_positive_substring():
    await add_knowledge("site", "общее", "Колледж основан в 1990 году")
    results = await find_relevant_chunks("поле")
    assert results == []

async def test_search_empty_knowledge_base():
    results = await find_relevant_chunks("грант")
    assert results == []

async def test_search_all_short_words():
    await add_knowledge("site", "общее", "да нет ок")
    results = await find_relevant_chunks("да")
    assert results == []

async def test_search_rank_order():
    await add_knowledge("site", "гранты", "грант для студентов")
    await add_knowledge("site", "гранты", "грант стипендия для отличников студентов")
    results = await find_relevant_chunks("грант для студентов")
    assert len(results) >= 1
    assert "грант" in results[0].lower()
