"""
Telegram-бот для дарк-кухни: открывает Mini App с меню и принимает заказы.

Установка зависимостей:
    pip install -r requirements.txt

Перед запуском заполни .env (см. .env.example):
    BOT_TOKEN=...       — токен от @BotFather
    WEBAPP_URL=...      — https-ссылка на захостенный index.html
    ADMIN_CHAT_ID=...   — твой chat_id (или id группы кухни), куда падают заказы

Запуск:
    python bot.py
"""

import asyncio
import json
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    MenuButtonWebApp,
)
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not BOT_TOKEN or not WEBAPP_URL:
    raise RuntimeError("Заполни BOT_TOKEN и WEBAPP_URL в файле .env")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.startup()
async def on_startup(bot: Bot):
    # Кнопка меню рядом со строкой ввода — открывает мини-апп в один тап
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="🍔 Меню", web_app=WebAppInfo(url=WEBAPP_URL))
    )


@dp.message(CommandStart())
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍔 Открыть меню", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer(
        "Привет! Это Дым и Дым 🔥\n\n"
        "Собери заказ в мини-приложении — кнопка ниже или в меню рядом со строкой ввода.",
        reply_markup=keyboard,
    )


@dp.message(F.web_app_data)
async def handle_order(message: Message):
    """Сюда прилетают данные из index.html (tg.sendData(...))."""
    try:
        data = json.loads(message.web_app_data.data)
    except (ValueError, AttributeError):
        await message.answer("Не получилось прочитать заказ, попробуй ещё раз 🙏")
        return

    items = data.get("items", [])
    total = data.get("total", 0)
    comment = data.get("comment", "").strip()

    lines = [f"🧾 Новый заказ от {message.from_user.full_name} (id {message.from_user.id})", ""]
    for it in items:
        lines.append(f"• {it['name']} × {it['qty']} — {it['price'] * it['qty']} ₽")
    lines.append("")
    lines.append(f"Итого: {total} ₽")
    if comment:
        lines.append(f"\nКомментарий: {comment}")

    order_text = "\n".join(lines)

    # Подтверждение клиенту
    await message.answer(
        f"Заказ принят! ✅\n\nИтого: {total} ₽\nМы свяжемся с тобой для подтверждения."
    )

    # Уведомление на кухню / админу
    if ADMIN_CHAT_ID:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=order_text)
    else:
        logging.info("ADMIN_CHAT_ID не задан, заказ выведен только в лог:\n%s", order_text)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
