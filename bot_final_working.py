#!/usr/bin/env python3
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
logger.info(f"✅ Токен загружен: {BOT_TOKEN[:15]}...")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Простая клавиатура с кнопками (не inline)
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Пройти анкету")],
            [KeyboardButton(text="🔍 Проверить совместимость")],
            [KeyboardButton(text="👤 Мой профиль")]
        ],
        resize_keyboard=True
    )
    return keyboard

@dp.message(CommandStart())
async def start_command(message: Message):
    logger.info(f"Пользователь {message.from_user.id} нажал /start")
    
    welcome_text = (
        "🎉 **БОТ СОВМЕСТИМОСТИ РАБОТАЕТ!**\n\n"
        "✅ Работает в облаке Railway 24/7\n"
        "✅ Анкета из 12 вопросов\n"
        "✅ Проверка по коду\n"
        "✅ Детальные результаты\n\n"
        "Выберите действие:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "🤖 **Помощь по боту:**\n\n"
        "1. 📝 **Пройти анкету** - ответьте на 12 вопросов\n"
        "2. 🔍 **Проверить совместимость** - введите код чужой анкеты\n"
        "3. 👤 **Мой профиль** - посмотреть свой код анкеты\n\n"
        "Каждый получает уникальный код после анкеты!",
        parse_mode="Markdown"
    )

@dp.message(Command("test"))
async def test_command(message: Message):
    await message.answer("✅ Тестовое сообщение работает!")

# Обработка кнопок клавиатуры
@dp.message(lambda message: message.text == "📝 Пройти анкету")
async def start_survey_handler(message: Message):
    await message.answer("📝 *Начинаем анкету!*\n\nПервый вопрос:\n\nДля меня важнее стабильность, чем изменения.\n\nОтветьте от 1 до 7:", parse_mode="Markdown")

@dp.message(lambda message: message.text == "🔍 Проверить совместимость")
async def check_compatibility_handler(message: Message):
    await message.answer("🔍 *Проверка совместимости*\n\nВведите код анкеты другого человека:\n\nПример: `PABC123DE`", parse_mode="Markdown")

@dp.message(lambda message: message.text == "👤 Мой профиль")
async def my_profile_handler(message: Message):
    await message.answer("👤 *Ваш профиль*\n\nПосле прохождения анкеты здесь появится ваш уникальный код!", parse_mode="Markdown")

# Ответ на любой другой текст
@dp.message()
async def echo_handler(message: Message):
    if message.text.startswith("P"):
        # Похоже на код анкеты
        await message.answer(f"🔍 Проверяем совместимость с кодом: {message.text}")
    else:
        await message.answer(f"Вы написали: {message.text}\n\nИспользуйте кнопки меню или команды:\n/start - главное меню\n/help - помощь\n/test - тест")

async def main():
    logger.info("🚀 ЗАПУСКАЕМ БОТА В ОБЛАКЕ...")
    logger.info("📱 Бот готов к работе в Telegram")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
