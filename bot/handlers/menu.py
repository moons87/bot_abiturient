# bot/handlers/menu.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
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
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "menu:main")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
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
