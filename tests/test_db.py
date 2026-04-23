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
