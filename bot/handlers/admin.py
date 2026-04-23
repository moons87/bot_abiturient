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
