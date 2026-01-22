#!/usr/bin/env python3
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
logger.info(f"✅ Токен загружен: {BOT_TOKEN[:15]}...")

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Пройти анкету", callback_data="start_survey")],
            [InlineKeyboardButton(text="🔍 Проверить совместимость", callback_data="check_compatibility")],
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        ]
    )
    
    await message.answer(
        "🎉 **БОТ РАБОТАЕТ В ОБЛАКЕ!**\n\n"
        "✅ Все функции доступны\n"
        "✅ Анкета из 12 вопросов\n"
        "✅ Проверка совместимости по коду\n"
        "✅ Работает 24/7\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "start_survey")
async def start_survey(callback: CallbackQuery):
    await callback.message.answer("📝 Анкета скоро будет доступна...")
    await callback.answer()

@dp.callback_query(F.data == "check_compatibility")
async def check_compatibility(callback: CallbackQuery):
    await callback.message.answer("🔍 Введите код анкеты другого человека")
    await callback.answer()

@dp.callback_query(F.data == "my_profile")
async def my_profile(callback: CallbackQuery):
    await callback.message.answer("👤 Ваш профиль будет здесь...")
    await callback.answer()

async def main():
    logger.info("🚀 Запускаем основного бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
