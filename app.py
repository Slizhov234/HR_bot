import os
import asyncio
import multiprocessing
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ===== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ =====
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")
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
    # --- Отпуска ---
    "vacation_days": "🏖 Основной трудовой отпуск — не менее 24 календарных дней (ст. 155 ТК РБ).",
    "vacation_transfer": "🏖 Отпуск можно перенести по соглашению с нанимателем. Если перенос связан с производственной необходимостью — наниматель обязан перенести с согласия работника.",
    "vacation_pay": "💰 Отпускные выплачиваются не позднее чем за 2 дня до начала отпуска.",
    "vacation_split": "🏖 Отпуск можно разделить на части. Одна часть должна быть не менее 14 календарных дней.",
    "vacation_compensation": "💰 При увольнении выплачивается денежная компенсация за все неиспользованные дни отпуска. В остальных случаях часть отпуска не менее 14 дней должна быть использована в текущем году.",
    "vacation_holidays": "🏖 Государственные праздники и праздничные дни в число календарных дней отпуска не включаются и не оплачиваются. Отпуск продлевается.",
    "vacation_unpaid": "🏖 Отпуск без сохранения зарплаты оформляется по заявлению с указанием причин и сроков. Наниматель может отказать, если нет оснований, предусмотренных законом.",
    "vacation_recall": "🏖 Отзыв из отпуска допускается только с согласия работника. Неиспользованная часть отпуска предоставляется в удобное время.",
    "vacation_parttime": "🏖 Совместителю отпуск предоставляется одновременно с отпуском по основной работе, если он работает в организации не первый год.",
    # --- Справки ---
    "cert_income": "📄 Справка о доходах выдаётся бесплатно в течение 5 дней со дня обращения (Указ № 200). Напиши заявление на имя руководителя.",
    "cert_stage": "📄 Справка о стаже выдаётся по заявлению в течение 5 дней.",
    "cert_copy": "📄 Копия трудовой книжки выдаётся в течение 3 рабочих дней по заявлению.",
    "cert_visa": "📄 Для справки на визу обычно нужна справка с места работы с указанием должности и зарплаты. Точный перечень зависит от требований посольства — уточняйте у кадровика.",
    "cert_credit": "📄 Для кредита нужна справка о доходах за последние 3–6 месяцев. Выдаётся бесплатно в течение 5 дней.",
    "cert_order": "📄 Выписка из приказа (о приёме, переводе, увольнении) выдаётся по заявлению в течение 3 рабочих дней.",
    # --- Командировки ---
    "trip_daily": "✈️ Суточные при командировке внутри Беларуси — 13 рублей в сутки (с 04.04.2026).",
    "trip_housing": "✈️ Норма возмещения за жильё: Минск и областные центры — 50 руб., районные центры — 25 руб., остальные — 20 руб. в сутки.",
    "trip_report": "✈️ По возвращении из командировки нужно сдать авансовый отчёт с подтверждающими документами в течение 3–5 рабочих дней.",
    "trip_oneday": "✈️ При однодневной командировке суточные выплачиваются, но расходы на жильё не возмещаются.",
    "trip_taxi": "✈️ Транспортные расходы в пределах места командировки оплачиваются за счёт суточных и отдельно не возмещаются (если иное не установлено нанимателем).",
    "trip_order": "✈️ Командировка оформляется приказом (распоряжением) нанимателя.",
    "trip_advance": "✈️ Авансовый отчёт сдаётся с подтверждающими документами: билеты, счета за жильё, чеки.",
    # --- Увольнение ---
    "fire_notice": "🚪 Об увольнении по собственному желанию нужно предупредить письменно за 1 месяц (ст. 40 ТК РБ).",
    "fire_docs": "🚪 При увольнении выдаётся трудовая книжка, справка о заработке для ФСЗН, копии приказов по требованию.",
    "fire_nowork": "🚪 Уволиться без отработки можно по соглашению с нанимателем. Некоторые категории (пенсионеры, при переезде) могут не отрабатывать.",
    "fire_probation": "🚪 Увольнение на испытательном сроке зависит от того, кто инициирует — работник или наниматель. Уточняйте у кадровика.",
    "fire_calc": "🚪 Расчёт (зарплата, компенсация за неиспользованный отпуск) выплачивается в день увольнения.",
    "fire_book": "🚪 Трудовая книжка выдаётся в день увольнения. Если работник отсутствует — направляется почтой с уведомлением.",
    # --- Обучение ---
    "study_pay": "🎓 Оплата обучения — по решению нанимателя. Может быть заключён ученический договор.",
    "study_work": "🎓 Если это предусмотрено договором, после обучения может быть установлен срок отработки.",
    "study_leave": "🎓 Учебный отпуск предоставляется при получении образования по направлению нанимателя или в случаях, предусмотренных законодательством.",
    "study_contract": "🎓 Ученический договор заключается на профессиональное обучение с возможностью последующей работы. Условия — у кадровика.",
    # --- Больничные ---
    "sick_pay": "🏥 Больничный оплачивается: первые 3 дня (при общем заболевании) — за счёт нанимателя, далее — за счёт ФСЗН.",
    "sick_percent": "🏥 Размер пособия зависит от стажа: до 5 лет — 60%, от 5 до 8 лет — 80%, свыше 8 лет — 100%.",
    "sick_vacation": "🏥 Если заболел в отпуске — отпуск продлевается или переносится на основании листка нетрудоспособности.",
    "sick_maternity": "🏥 Пособие по беременности и родам назначается в течение 10 дней после предоставления больничного, выплачивается в ближайший день зарплаты.",
    "sick_child": "🏥 Больничный по уходу за ребёнком оформляется листком нетрудоспособности.",
    # --- Приём на работу ---
    "hire_docs": "👔 При приёме нужны: паспорт, трудовая книжка (если есть), документ об образовании, военный билет (при необходимости), страховое свидетельство.",
    "hire_contract": "👔 Трудовой договор заключается в письменной форме, в двух экземплярах.",
    "hire_probation": "👔 Испытательный срок может быть до 3 месяцев (для рабочих — до 1 месяца, для руководителей — до 6 месяцев).",
    "hire_contract_form": "👔 Контракт — разновидность трудового договора с дополнительными условиями (срок, гарантии/компенсации). Порядок — по Положению о контрактной форме.",
    # --- Рабочее время ---
    "time_norm": "⏰ Нормальная продолжительность рабочего времени — не более 40 часов в неделю.",
    "time_lunch": "⏰ В течение рабочего дня предоставляется перерыв для отдыха и питания не более 2 часов.",
    "time_overtime": "⏰ Сверхурочная работа — только с письменного согласия работника (в установленных случаях) и с приказом. Оплата — в повышенном размере или компенсация отдыхом.",
    "time_parttime": "⏰ Работа по совместительству разрешена с учётом ограничений (не более половины нормы рабочего времени по общему правилу).",
    "time_absent": "⏰ Прогулом считается отсутствие на работе без уважительных причин более 4 часов подряд в течение рабочего дня.",
    # --- Контакты ---
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
    builder.button(text="🏥 Больничные", callback_data="menu_sick")
    builder.button(text="👔 Приём на работу", callback_data="menu_hire")
    builder.button(text="⏰ Рабочее время", callback_data="menu_time")
    builder.button(text="📞 Связаться с кадровиком", callback_data="contact")
    builder.adjust(2)
    return builder.as_markup()

def vacation_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Сколько дней отпуска?", callback_data="vacation_days")
    builder.button(text="Как перенести отпуск?", callback_data="vacation_transfer")
    builder.button(text="Когда выплачивают отпускные?", callback_data="vacation_pay")
    builder.button(text="Можно ли разделить отпуск?", callback_data="vacation_split")
    builder.button(text="Компенсация за неиспользованный отпуск", callback_data="vacation_compensation")
    builder.button(text="Праздничные дни в отпуске", callback_data="vacation_holidays")
    builder.button(text="Отпуск без сохранения зарплаты", callback_data="vacation_unpaid")
    builder.button(text="Отзыв из отпуска", callback_data="vacation_recall")
    builder.button(text="Отпуск совместителю", callback_data="vacation_parttime")
    builder.button(text="⬅️ Назад", callback_data="menu_main")
    builder.adjust(1)
    return builder.as_markup()

def cert_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Справка о доходах", callback_data="cert_income")
    builder.button(text="Справка о стаже", callback_data="cert_stage")
    builder.button(text="Копия трудовой книжки", callback_data="cert_copy")
    builder.button(text="Справка на визу", callback_data="cert_visa")
    builder.button(text="Справка для кредита", callback_data="cert_credit")
    builder.button(text="Выписка из приказа", callback_data="cert_order")
    builder.button(text="⬅️ Назад", callback_data="menu_main")
    builder.adjust(1)
    return builder.as_markup()

def trip_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Сколько суточных?", callback_data="trip_daily")
    builder.button(text="Нормы возмещения за жильё", callback_data="trip_housing")
    builder.button(text="Как отчитаться?", callback_data="trip_report")
    builder.button(text="Однодневная командировка", callback_data="trip_oneday")
    builder.button(text="Такси в командировке", callback_data="trip_taxi")
    builder.button(text="Приказ на командировку", callback_data="trip_order")
    builder.button(text="Авансовый отчёт", callback_data="trip_advance")
    builder.button(text="⬅️ Назад", callback_data="menu_main")
    builder.adjust(1)
    return builder.as_markup()

def fire_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Как уволиться?", callback_data="fire_notice")
    builder.button(text="Что выдаётся при увольнении?", callback_data="fire_docs")
    builder.button(text="Увольнение без отработки", callback_data="fire_nowork")
    builder.button(text="Увольнение на испытательном сроке", callback_data="fire_probation")
    builder.button(text="Расчёт при увольнении", callback_data="fire_calc")
    builder.button(text="Трудовая книжка", callback_data="fire_book")
    builder.button(text="⬅️ Назад", callback_data="menu_main")
    builder.adjust(1)
    return builder.as_markup()

def study_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Оплачивает ли организация обучение?", callback_data="study_pay")
    builder.button(text="Нужно ли отрабатывать?", callback_data="study_work")
    builder.button(text="Учебный отпуск", callback_data="study_leave")
    builder.button(text="Ученический договор", callback_data="study_contract")
    builder.button(text="⬅️ Назад", callback_data="menu_main")
    builder.adjust(1)
    return builder.as_markup()

def sick_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Кто платит больничный?", callback_data="sick_pay")
    builder.button(text="Как оплачивается больничный?", callback_data="sick_percent")
    builder.button(text="Больничный в отпуске", callback_data="sick_vacation")
    builder.button(text="Декретные", callback_data="sick_maternity")
    builder.button(text="Больничный по уходу за ребёнком", callback_data="sick_child")
    builder.button(text="⬅️ Назад", callback_data="menu_main")
    builder.adjust(1)
    return builder.as_markup()

def hire_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Документы при приёме", callback_data="hire_docs")
    builder.button(text="Трудовой договор", callback_data="hire_contract")
    builder.button(text="Испытательный срок", callback_data="hire_probation")
    builder.button(text="Что такое контракт?", callback_data="hire_contract_form")
    builder.button(text="⬅️ Назад", callback_data="menu_main")
    builder.adjust(1)
    return builder.as_markup()

def time_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Норма рабочего времени", callback_data="time_norm")
    builder.button(text="Обеденный перерыв", callback_data="time_lunch")
    builder.button(text="Сверхурочная работа", callback_data="time_overtime")
    builder.button(text="Работа по совместительству", callback_data="time_parttime")
    builder.button(text="Что считается прогулом?", callback_data="time_absent")
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

# --- Обработчики меню ---

@dp.callback_query(F.data == "menu_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👋 Главное меню. Выбери раздел:",
        reply_markup=main_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_vacation")
async def show_vacation(callback: types.CallbackQuery):
    await callback.message.edit_text("🏖 Отпуска. Что интересует?", reply_markup=vacation_menu())
    await callback.answer()

@dp.callback_query(F.data == "menu_cert")
async def show_cert(callback: types.CallbackQuery):
    await callback.message.edit_text("📄 Справки. Что интересует?", reply_markup=cert_menu())
    await callback.answer()

@dp.callback_query(F.data == "menu_trip")
async def show_trip(callback: types.CallbackQuery):
    await callback.message.edit_text("✈️ Командировки. Что интересует?", reply_markup=trip_menu())
    await callback.answer()

@dp.callback_query(F.data == "menu_fire")
async def show_fire(callback: types.CallbackQuery):
    await callback.message.edit_text("🚪 Увольнение. Что интересует?", reply_markup=fire_menu())
    await callback.answer()

@dp.callback_query(F.data == "menu_study")
async def show_study(callback: types.CallbackQuery):
    await callback.message.edit_text("🎓 Обучение. Что интересует?", reply_markup=study_menu())
    await callback.answer()

@dp.callback_query(F.data == "menu_sick")
async def show_sick(callback: types.CallbackQuery):
    await callback.message.edit_text("🏥 Больничные. Что интересует?", reply_markup=sick_menu())
    await callback.answer()

@dp.callback_query(F.data == "menu_hire")
async def show_hire(callback: types.CallbackQuery):
    await callback.message.edit_text("👔 Приём на работу. Что интересует?", reply_markup=hire_menu())
    await callback.answer()

@dp.callback_query(F.data == "menu_time")
async def show_time(callback: types.CallbackQuery):
    await callback.message.edit_text("⏰ Рабочее время. Что интересует?", reply_markup=time_menu())
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
