import os
import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from openai import OpenAI

# ===== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ RENDER =====
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# =======================================

# --- Flask для Render (держит порт открытым) ---
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running"

@app.route("/health")
def health():
    return "OK"

# --- Логика бота ---
KNOWLEDGE_FILE = "knowledge.txt"

def load_knowledge():
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "База знаний пока пуста."

KNOWLEDGE = load_knowledge()

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

SYSTEM_PROMPT = f"""Ты — кадровый помощник. Отвечай ТОЛЬКО на основе базы знаний ниже.
Если ответа в базе нет — скажи: "Этого нет в моей базе. Уточните у кадровика."
Не выдумывай, не давай юридических заключений.

БАЗА ЗНАНИЙ:
{KNOWLEDGE}
"""

user_histories = {}
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет. Я кадровый бот. Спрашивай по делу.")

@dp.message(Command("reset"))
async def reset(message: types.Message):
    user_histories[message.from_user.id] = []
    await message.answer("История очищена.")

@dp.message()
async def handle(message: types.Message):
    user_id = message.from_user.id
    text = message.text or ""

    if user_id not in user_histories:
        user_histories[user_id] = []
    history = user_histories[user_id]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": text})

    try:
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=messages,
            temperature=0.3,
        )
        answer = response.choices[0].message.content

        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": answer})
        if len(history) > 20:
            history[:] = history[-20:]

        await message.answer(answer)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

def run_bot():
    """Запускает polling в отдельном потоке с собственным event loop."""
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    # Бот — в фоне, чтобы Flask мог занять порт
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Flask — на порту, который даёт Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)