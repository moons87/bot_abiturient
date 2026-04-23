# bot/keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Специальности", callback_data="section:специальности")],
        [InlineKeyboardButton(text="💰 Гранты", callback_data="section:гранты")],
        [InlineKeyboardButton(text="🏠 Общежитие", callback_data="section:общежитие")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="faq:list")],
        [InlineKeyboardButton(text="📅 Записаться на мероприятие", callback_data="excursion:list")],
        [InlineKeyboardButton(text="🎯 Профориентационный тест", callback_data="proftest:start")],
    ])

def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")]
    ])

def faq_keyboard(faqs: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f["question"][:50], callback_data=f"faq:show:{f['id']}")]
        for f in faqs
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def excursion_dates_keyboard(dates: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for d in dates:
        remaining = d["max_slots"] - d["current_slots"]
        label = f"📅 {d['date']} {d['time']} — {d['type']} (мест: {remaining})"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"excursion:choose:{d['id']}")])
    buttons.append([InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def proftest_answer_keyboard(question_idx: int, options: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{key}) {val}", callback_data=f"pt:{question_idx}:{key}")]
        for key, val in options.items()
    ])

def admin_dates_keyboard(dates: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"❌ {d['date']} {d['time']} — {d['type']}",
            callback_data=f"admin:deldate:{d['id']}",
        )]
        for d in dates
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons or [[]])

def admin_faq_keyboard(faqs: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"❌ {f['question'][:40]}", callback_data=f"admin:delfaq:{f['id']}")]
        for f in faqs
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons or [[]])
