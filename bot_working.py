#!/usr/bin/env python3
import os
import sys
import logging
import asyncio

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ХАРДКОД ТОКЕНА (только для теста!)
BOT_TOKEN = "8226006171:AAHxOe8FpTrHG-o3kyerUTkkwCvil81htX4"

logger.info("=" * 50)
logger.info("🤖 ТЕСТОВЫЙ БОТ ЗАПУСКАЕТСЯ")
logger.info("=" * 50)
logger.info(f"Используется токен: {BOT_TOKEN[:15]}...")

try:
    from aiogram import Bot, Dispatcher
    from aiogram.filters import CommandStart
    from aiogram.types import Message
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    @dp.message(CommandStart())
    async def start_handler(message: Message):
        await message.answer(
            "🎉 Бот работает в облаке Railway!\n\n"
            "✅ Анкета совместимости готова\n"
            "✅ Проверка по коду работает\n"
            "✅ Результаты с прогнозами\n\n"
            "Нажмите /menu для начала"
        )
    
    async def main():
        logger.info("🚀 Запускаем polling...")
        await dp.start_polling(bot)
    
    if __name__ == "__main__":
        asyncio.run(main())
        
except Exception as e:
    logger.error(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
