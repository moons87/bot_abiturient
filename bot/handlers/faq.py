# bot/handlers/faq.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from knowledge.db import get_all_faq, get_faq_by_id
from bot.keyboards import faq_keyboard, back_to_menu_keyboard

router = Router()

@router.callback_query(F.data == "faq:list")
async def faq_list_handler(callback: CallbackQuery):
    faqs = await get_all_faq()
    if not faqs:
        await callback.message.edit_text(
            "Раздел FAQ пока пуст. Задайте вопрос — мы добавим!",
            reply_markup=back_to_menu_keyboard(),
        )
        return
    await callback.message.edit_text(
        "Часто задаваемые вопросы — выберите нужный:",
        reply_markup=faq_keyboard(faqs),
    )

@router.callback_query(F.data.startswith("faq:show:"))
async def faq_show_handler(callback: CallbackQuery):
    faq_id = int(callback.data.split(":")[2])
    faq = await get_faq_by_id(faq_id)
    if not faq:
        await callback.answer("Вопрос не найден", show_alert=True)
        return
    await callback.message.edit_text(
        f"❓ {faq['question']}\n\n✅ {faq['answer']}",
        reply_markup=back_to_menu_keyboard(),
    )
