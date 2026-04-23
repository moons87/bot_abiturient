# ai/claude_client.py
import logging
import os
import anthropic

logger = logging.getLogger(__name__)
client = anthropic.AsyncAnthropic(api_key=os.getenv("CLAUDE_API_KEY"))

MODEL = "claude-haiku-4-5-20251001"

FALLBACK_ANSWER = "Не удалось получить ответ. Попробуйте позже или напишите администратору."

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
    try:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": question}],
        )
        return response.content[0].text
    except anthropic.APIError as e:
        logger.error("Claude API error in ask_question: %s", e)
        return FALLBACK_ANSWER

async def generate_proftest_report(answers: list[dict], specialties: list[str]) -> str:
    answers_text = "\n".join(f"- {a['question']}: {a['answer']}" for a in answers)
    specialties_text = "\n".join(f"- {s}" for s in specialties)
    prompt = (
        f"Абитуриент прошёл профориентационный тест. Его ответы:\n{answers_text}\n\n"
        f"Специальности колледжа:\n{specialties_text}\n\n"
        "Напиши развёрнутый отчёт (300-400 слов): проанализируй интересы и сильные стороны, "
        "порекомендуй 2-3 подходящие специальности с объяснением. Пиши дружелюбно."
    )
    try:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except anthropic.APIError as e:
        logger.error("Claude API error in generate_proftest_report: %s", e)
        return FALLBACK_ANSWER
