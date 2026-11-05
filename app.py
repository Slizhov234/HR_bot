import os
import asyncio
import multiprocessing
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ===== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ =====
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8719916635:AAGJNzRd23x1j-5pqVuj-Hj7EEy0gSE4uZo")
# =================================

# --- Flask для Render ---
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running"

@app.route("/health")
def health():
    return "OK"

# --- Тексты ответов ---
TEXTS = {
    "vacation_days": "🏖 Основной трудовой отпуск — не менее 24 календарных дней (ст. 155 ТК РБ).",
    "vacation_transfer": "🏖 Отпуск можно перенести по соглашению с нанимателем. Если перенос связан с производственной необходимостью — наниматель обязан перенести с согласия работника.",
    "vacation_pay": "💰 Отпускные выплачиваются не позднее чем за 2 дня до начала отпуска.",
    "vacation_split": "🏖 Отпуск можно разделить на части. Одна часть должна быть не менее 14 календарных дней.",
    "cert_income": "📄 Справка о доходах выдаётся бесплатно в течение 5 дней со дня обращения (Указ № 200). Напиши заявление на имя руководителя.",
    "cert_stage": "📄 Справка о стаже выдаётся по заявлению в течение 5 дней.",
    "cert_copy": "📄 Копия трудовой книжки выдаётся в течение 3 рабочих дней по заявлению.",
    "trip_daily": "✈️ Суточные при командировке внутри Беларуси — 13 рублей в сутки (с 04.04.2026).",
    "trip_housing": "✈️ Норма возмещения за жильё: Минск и областные центры — 50 руб., районные центры — 25 руб., остальные — 20 руб. в сутки.",
    "trip_report": "✈️ По возвращении из командировки нужно сдать авансовый отчёт с подтверждающими документами в течение 3-5 рабочих дней.",
    "fire_notice": "🚪 Об увольнении по собственному желанию нужно предупредить письменно за 1 месяц (ст. 40 ТК РБ).",
    "fire_docs": "🚪 При увольнении выдаётся трудовая книжка, справка о заработке для ФСЗН, копии приказов по требованию.",
    "study_pay": "🎓 Оплата обучения — по решению нанимателя. Может быть заключён ученический договор.",
    "study_work": "🎓 Если это предусмотрено договором, после обучения может быть установлен срок отработки.",
    "contact": "📞 Связаться с кадровиком:\nТелефон: +375 (XX) XXX-XX-XX\nEmail: hr@example.by\nКабинет: 123",
}

# --- Клавиатуры ---

def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏖 Отпуска", callback_data="menu_vacation")
    builder.button(text="📄 Справки", callback_data="menu_cert")
    builder.button(text="✈️ Командировки", callback_data="menu_trip")
    builder.button(text="🚪 Увольнение", callback_data="menu_fire")
    builder.button(text="🎓 Обучение", callback_data="menu_study")
    builder.button(text="📞 Связаться с кадровиком", callback_data="contact")
    builder.adjust(2)
    return builder.as_markup()

def vacation_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Сколько дней отпуска?", callback_data="vacation_days")
    builder.button(text="Как перенести отпуск?", callback_data="vacation_transfer")
    builder.button(text="Когда выплачивают отпускные?", callback_data="vacation_pay")
    builder.button(text="Можно ли разделить отпуск?", callback_data="vacation_split")
    builder.button(text="⬅️ Назад", callback_data="menu_main")
    builder.adjust(1)
    return builder.as_markup()

def cert_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Справка о доходах", callback_data="cert_income")
    builder.button(text="Справка о стаже", callback_data="cert_stage")
    builder.button(text="Копия трудовой книжки", callback_data="cert_copy")
    builder.button(text="⬅️ Назад", callback_data="menu_main")
    builder.adjust(1)
    return builder.as_markup()

def trip_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Сколько суточных?", callback_data="trip_daily")
    builder.button(text="Нормы возмещения за жильё", callback_data="trip_housing")
    builder.button(text="Как отчитаться?", callback_data="trip_report")
    builder.button(text="⬅️ Назад", callback_data="menu_main")
    builder.adjust(1)
    return builder.as_markup()

def fire_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Как уволиться?", callback_data="fire_notice")
    builder.button(text="Что выдаётся при увольнении?", callback_data="fire_docs")
    builder.button(text="⬅️ Назад", callback_data="menu_main")
    builder.adjust(1)
    return builder.as_markup()

def study_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Оплачивает ли организация обучение?", callback_data="study_pay")
    builder.button(text="Нужно ли отрабатывать?", callback_data="study_work")
    builder.button(text="⬅️ Назад", callback_data="menu_main")
    builder.adjust(1)
    return builder.as_markup()

# --- Бот ---
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я кадровый помощник. Выбери раздел:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "menu_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👋 Главное меню. Выбери раздел:",
        reply_markup=main_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_vacation")
async def show_vacation(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🏖 Отпуска. Что интересует?",
        reply_markup=vacation_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_cert")
async def show_cert(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📄 Справки. Что интересует?",
        reply_markup=cert_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_trip")
async def show_trip(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "✈️ Командировки. Что интересует?",
        reply_markup=trip_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_fire")
async def show_fire(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🚪 Увольнение. Что интересует?",
        reply_markup=fire_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_study")
async def show_study(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎓 Обучение. Что интересует?",
        reply_markup=study_menu()
    )
    await callback.answer()

# --- Обработка текстовых ответов ---
@dp.callback_query(F.data.in_(TEXTS.keys()))
async def show_answer(callback: types.CallbackQuery):
    text = TEXTS[callback.data]
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="menu_main")
    builder.adjust(1)
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# --- Fallback на текстовые сообщения ---
@dp.message()
async def fallback(message: types.Message):
    await message.answer(
        "Пожалуйста, выбери раздел из меню:",
        reply_markup=main_menu()
    )

# --- Запуск ---
def run_bot():
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    bot_process = multiprocessing.Process(target=run_bot)
    bot_process.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)