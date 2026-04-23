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
    current = data["current"]
    if q_idx != current or q_idx >= len(QUESTIONS):
        await callback.answer()
        return
    answers = data["answers"]
    q = QUESTIONS[q_idx]
    answers.append({"question": q["text"], "answer": q["options"][chosen_key]})
    next_idx = q_idx + 1
    if next_idx >= len(QUESTIONS):
        await state.clear()
        await callback.message.edit_text("⏳ Анализирую ваши ответы, подождите 10-20 секунд...")
        try:
            report = await generate_proftest_report(answers, COLLEGE_SPECIALTIES)
        except Exception:
            report = "Не удалось сформировать отчёт. Попробуйте позже или напишите администратору."
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
