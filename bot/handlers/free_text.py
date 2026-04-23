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
