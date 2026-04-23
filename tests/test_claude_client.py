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

async def test_ask_question_returns_fallback_on_api_error():
    import anthropic as ant
    with patch("ai.claude_client.client.messages.create", new=AsyncMock(side_effect=ant.APIConnectionError(request=None))):
        result = await ask_question("тест", "контекст")
    assert result == "Не удалось получить ответ. Попробуйте позже или напишите администратору."
