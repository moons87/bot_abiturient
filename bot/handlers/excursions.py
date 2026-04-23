# bot/handlers/excursions.py
import os
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from knowledge.db import (
    get_active_excursion_dates, get_excursion_date_by_id, register_for_excursion,
)
from bot.keyboards import excursion_dates_keyboard, back_to_menu_keyboard

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))

class ExcursionStates(StatesGroup):
    choosing_date = State()
    entering_name = State()
    entering_phone = State()

@router.callback_query(F.data == "excursion:list")
async def excursion_list(callback: CallbackQuery, state: FSMContext):
    dates = await get_active_excursion_dates()
    available = [d for d in dates if d["current_slots"] < d["max_slots"]]
    if not available:
        await callback.message.edit_text(
            "Ближайших мероприятий пока нет. Следите за обновлениями!",
            reply_markup=back_to_menu_keyboard(),
        )
        return
    await state.set_state(ExcursionStates.choosing_date)
    await callback.message.edit_text(
        "Выберите дату мероприятия:",
        reply_markup=excursion_dates_keyboard(available),
    )

@router.callback_query(ExcursionStates.choosing_date, F.data.startswith("excursion:choose:"))
async def excursion_choose_date(callback: CallbackQuery, state: FSMContext):
    date_id = int(callback.data.split(":")[2])
    date_info = await get_excursion_date_by_id(date_id)
    if not date_info:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return
    label = f"{date_info['date']} {date_info['time']} — {date_info['type']}"
    await state.update_data(date_id=date_id, date_label=label)
    await state.set_state(ExcursionStates.entering_name)
    await callback.message.edit_text(f"Вы выбрали: {label}\n\nВведите ваше ФИО:")

@router.message(ExcursionStates.entering_name)
async def excursion_enter_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите текстом ваше ФИО:")
        return
    await state.update_data(name=message.text)
    await state.set_state(ExcursionStates.entering_phone)
    await message.answer("Введите ваш номер телефона:")

@router.message(ExcursionStates.entering_phone)
async def excursion_enter_phone(message: Message, state: FSMContext, bot: Bot):
    if not message.text:
        await message.answer("Пожалуйста, введите номер телефона текстом:")
        return
    data = await state.get_data()
    await state.clear()
    try:
        await register_for_excursion(data["date_id"], data["name"], message.text, message.from_user.id)
    except ValueError:
        await message.answer(
            "К сожалению, места на это мероприятие закончились.",
            reply_markup=back_to_menu_keyboard(),
        )
        return
    await message.answer(
        f"✅ Вы успешно записаны!\n\n"
        f"📅 {data['date_label']}\n"
        f"👤 {data['name']}\n"
        f"📞 {message.text}\n\nЖдём вас!",
        reply_markup=back_to_menu_keyboard(),
    )
    if ADMIN_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
        await bot.send_message(
            ADMIN_ID,
            f"📋 Новая заявка на мероприятие!\n\n"
            f"📅 {data['date_label']}\n"
            f"👤 ФИО: {data['name']}\n"
            f"📞 Телефон: {message.text}\n"
            f"🔗 Telegram: {username}",
        )
