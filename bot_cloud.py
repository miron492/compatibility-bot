#!/usr/bin/env python3
"""
Бот для проверки совместимости пар
Безопасная версия с загрузкой токена из переменных окружения
"""

import os
import sys
import asyncio
import random
import string
import json
import sqlite3
import datetime
from typing import Dict, List, Set, Optional, Tuple
import logging

# Сначала настроим логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === БЕЗОПАСНАЯ ЗАГРУЗКА ТОКЕНА ===
def load_bot_token():
    """
    Безопасно загружает токен бота из переменных окружения
    Никогда не хранит токен в коде
    """
    
    # Пробуем получить токен из переменных окружения
    token = os.getenv("BOT_TOKEN")
    
    if not token:
        print("\n" + "="*60)
        print("🚨 ОШИБКА: ТОКЕН БОТА НЕ НАЙДЕН!")
        print("="*60)
        print("\nДля работы бота нужно настроить токен:")
        print("\n1. ДЛЯ ЛОКАЛЬНОГО ЗАПУСКА:")
        print("   Создайте файл .env в папке с ботом")
        print("   Добавьте в него: BOT_TOKEN=ваш_токен")
        print("   Пример: BOT_TOKEN=123456789:ABCdefGHIjklMNoPQRStuVWXyz")
        
        print("\n2. ДЛЯ ЗАПУСКА В ОБЛАКЕ (Railway/Render):")
        print("   Добавьте переменную окружения BOT_TOKEN")
        print("   в настройках вашего облачного сервиса")
        
        print("\n3. Как получить токен:")
        print("   - Откройте Telegram")
        print("   - Найдите @BotFather")
        print("   - Создайте нового бота или получите токен существующего")
        print("="*60)
        
        # Даем время прочитать сообщение
        import time
        time.sleep(5)
        sys.exit(1)  # Завершаем работу с ошибкой
    
    # Проверяем, что токен выглядит правильно
    if ":" not in token:
        logger.error(f"❌ Неверный формат токена. Токен должен содержать ':'")
        logger.error(f"   Получено: {token[:20]}...")
        sys.exit(1)
    
    logger.info(f"✅ Токен успешно загружен (первые 10 символов): {token[:10]}...")
    return token

# Загружаем токен
BOT_TOKEN = load_bot_token()

# Теперь импортируем aiogram (после загрузки токена)
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command

# Инициализируем бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === БАЗА ДАННЫХ SQLite ===
def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect('compatibility_bot.db')
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            profile_code TEXT UNIQUE,
            answers_json TEXT,
            completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица проверок совместимости
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compatibility_checks (
            check_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER,
            user2_id INTEGER,
            user1_code TEXT,
            user2_code TEXT,
            total_percent REAL,
            results_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ База данных инициализирована")

# Инициализируем БД при запуске
init_database()

def get_db_connection():
    """Получить соединение с базой данных"""
    conn = sqlite3.connect('compatibility_bot.db')
    conn.row_factory = sqlite3.Row
    return conn

# === АНКЕТА СОВМЕСТИМОСТИ ===
questions = [
    # БЛОК 1: ЦЕННОСТИ И ЖИЗНЕННЫЕ ОРИЕНТИРЫ
    {"id": 1, "block": 1, "weight": 20, "text": "Для меня важнее стабильность, чем постоянные изменения.", "type": "scale"},
    {"id": 2, "block": 1, "weight": 20, "text": "Я считаю семью приоритетом по сравнению с карьерой.", "type": "scale"},
    
    # БЛОК 2: ЦЕЛИ И ВЕКТОР ЖИЗНИ
    {"id": 3, "block": 2, "weight": 15, "text": "Я понимаю, каким хочу видеть свою жизнь через 5 лет.", "type": "scale"},
    {"id": 4, "block": 2, "weight": 15, "text": "Я готов(а) адаптировать свои цели ради отношений.", "type": "scale"},
    
    # БЛОК 3: ЭМОЦИОНАЛЬНАЯ МОДЕЛЬ И БЛИЗОСТЬ
    {"id": 5, "block": 3, "weight": 15, "text": "Мне важно регулярно обсуждать чувства.", "type": "scale"},
    {"id": 6, "block": 3, "weight": 15, "text": "В конфликте я скорее закрываюсь, чем иду на контакт.", "type": "scale"},
    
    # БЛОК 4: КОНФЛИКТЫ И ОТВЕТСТВЕННОСТЬ
    {"id": 7, "block": 4, "weight": 15, "text": "Я умею признавать свои ошибки.", "type": "scale"},
    {"id": 8, "block": 4, "weight": 15, "text": "Для меня важно быть правым(ой).", "type": "scale"},
    
    # БЛОК 5: БЫТ, ДЕНЬГИ, РОЛИ
    {"id": 9, "block": 5, "weight": 15, "text": "Мне важно чёткое распределение обязанностей.", "type": "scale"},
    {"id": 10, "block": 5, "weight": 15, "text": "Совместный бюджет — хорошая идея.", "type": "scale"},
    
    # БЛОК 6: ЛИЧНЫЕ ГРАНИЦЫ И СВОБОДА
    {"id": 11, "block": 6, "weight": 10, "text": "Мне нужно много личного пространства.", "type": "scale"},
    {"id": 12, "block": 6, "weight": 10, "text": "Я нормально отношусь к отдельным увлечениям партнёра.", "type": "scale"},
]

block_names = {
    1: "Ценности и жизненные ориентиры",
    2: "Цели и вектор жизни", 
    3: "Эмоциональная модель и близость",
    4: "Конфликты и ответственность",
    5: "Быт, деньги, роли",
    6: "Личные границы и свобода"
}

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def generate_profile_code():
    """Сгенерировать уникальный код профиля"""
    while True:
        code = "P" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE profile_code = ?", (code,))
        count = cursor.fetchone()[0]
        conn.close()
        if count == 0:
            return code

def get_user_profile(user_id):
    """Получить профиль пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "user_id": row["user_id"],
            "username": row["username"],
            "first_name": row["first_name"],
            "profile_code": row["profile_code"],
            "answers": json.loads(row["answers_json"]) if row["answers_json"] else {},
            "completed": bool(row["completed"]),
            "created_at": row["created_at"],
            "last_used": row["last_used"]
        }
    return None

def save_user_profile(user_id, username, first_name, answers=None, completed=False):
    """Сохранить или обновить профиль пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    existing = cursor.fetchone()
    
    if existing:
        if answers is not None:
            cursor.execute('''
                UPDATE users 
                SET answers_json = ?, completed = ?, last_used = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (json.dumps(answers), 1 if completed else 0, user_id))
    else:
        profile_code = generate_profile_code()
        answers_json = json.dumps(answers) if answers else None
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, profile_code, answers_json, completed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, profile_code, answers_json, 1 if completed else 0))
    
    conn.commit()
    conn.close()

def get_profile_by_code(profile_code):
    """Получить профиль по коду"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE profile_code = ? AND completed = 1", 
        (profile_code,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "user_id": row["user_id"],
            "username": row["username"],
            "first_name": row["first_name"],
            "profile_code": row["profile_code"],
            "answers": json.loads(row["answers_json"]) if row["answers_json"] else {},
            "completed": bool(row["completed"])
        }
    return None

def calculate_compatibility(answers1, answers2):
    """Рассчитать совместимость по ответам двух пользователей"""
    
    block_scores = {i: {"total": 0, "max": 0} for i in range(1, 7)}
    total_score = 0
    total_max = 0
    
    for question in questions:
        q_id = question["id"]
        block = question["block"]
        weight = question["weight"]
        
        if q_id not in answers1 or q_id not in answers2:
            continue
            
        answer1 = answers1[q_id]
        answer2 = answers2[q_id]
        
        diff = abs(answer1 - answer2)
        match_score = 1 - (diff / 6)
        
        question_score = match_score * weight
        block_scores[block]["total"] += question_score
        block_scores[block]["max"] += weight
        
        total_score += question_score
        total_max += weight
    
    if total_max == 0:
        compatibility_percent = 0
    else:
        compatibility_percent = round((total_score / total_max * 100), 1)
    
    block_percents = {}
    for block_num in range(1, 7):
        if block_scores[block_num]["max"] > 0:
            percent = round((block_scores[block_num]["total"] / block_scores[block_num]["max"]) * 100, 1)
        else:
            percent = 0
            
        block_percents[block_num] = {
            "percent": percent,
            "name": block_names.get(block_num, f"Блок {block_num}")
        }
    
    strong_areas = [(block_num, data) for block_num, data in block_percents.items() if data["percent"] >= 75]
    growth_areas = [(block_num, data) for block_num, data in block_percents.items() if 50 <= data["percent"] < 75]
    risk_areas = [(block_num, data) for block_num, data in block_percents.items() if data["percent"] < 50]
    
    forecasts = []
    if compatibility_percent >= 80:
        forecasts = ["💞 Высокая совместимость!", "🤝 Глубокое взаимопонимание"]
    elif compatibility_percent >= 60:
        forecasts = ["✨ Хорошая база для отношений", "⚖️ Возможны разногласия"]
    elif compatibility_percent >= 40:
        forecasts = ["⚠️ Средняя совместимость", "🔄 Потребуются усилия"]
    else:
        forecasts = ["🚨 Низкая совместимость", "💔 Возможны конфликты"]
    
    recommendations = ["💬 Обсуждайте важные темы", "👂 Учитесь слушать партнера"]
    
    return {
        "total_percent": compatibility_percent,
        "block_percents": block_percents,
        "strong_areas": strong_areas,
        "growth_areas": growth_areas,
        "risk_areas": risk_areas,
        "forecasts": forecasts,
        "recommendations": recommendations
    }

# === СЕССИИ ПОЛЬЗОВАТЕЛЕЙ ===
user_sessions = {}

# === ОБРАБОТЧИКИ КОМАНД ===
@dp.message(CommandStart())
async def start_handler(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    
    save_user_profile(user_id, username, first_name)
    profile = get_user_profile(user_id)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Пройти анкету", callback_data="start_survey")],
            [InlineKeyboardButton(text="🔍 Проверить совместимость", callback_data="check_compatibility")],
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        ]
    )
    
    welcome_text = "👋 Добро пожаловать в бот для проверки совместимости!\n\n"
    
    if profile and profile.get("completed"):
        welcome_text += f"✅ У вас есть заполненная анкета.\n🆔 Код вашей анкеты: <code>{profile['profile_code']}</code>\n\n"
        welcome_text += "Вы можете:\n• Поделиться кодом с другими\n• Проверить совместимость с чужой анкетой"
    else:
        welcome_text += "У вас еще нет заполненной анкеты.\nПройти её можно сейчас или позже."
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data == "my_profile")
async def my_profile_handler(callback: CallbackQuery):
    """Показать профиль пользователя"""
    user_id = callback.from_user.id
    profile = get_user_profile(user_id)
    
    if not profile or not profile.get("completed"):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📝 Пройти анкету", callback_data="start_survey")]
            ]
        )
        await callback.message.answer(
            "У вас еще нет заполненной анкеты.\nСначала пройдите анкету, чтобы получить код.",
            reply_markup=keyboard
        )
    else:
        profile_code = profile["profile_code"]
        
        profile_text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"🆔 Код анкеты: <code>{profile_code}</code>\n"
            f"📅 Создана: {profile['created_at'][:10]}\n\n"
            f"<b>Как использовать код:</b>\n"
            f"1. Поделитесь этим кодом с другим человеком\n"
            f"2. Он вводит его в разделе 'Проверить совместимость'\n"
            f"3. Вы сразу получите результат!\n\n"
            f"<i>Код можно использовать многократно</i>"
        )
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📤 Поделиться кодом", 
                                     url=f"https://t.me/share/url?url=Мой%20код%20анкеты%20совместимости:%20{profile_code}")],
                [InlineKeyboardButton(text="🔍 Проверить по коду", callback_data="check_compatibility")],
            ]
        )
        
        await callback.message.answer(profile_text, reply_markup=keyboard, parse_mode="HTML")
    
    await callback.answer()

@dp.callback_query(F.data == "check_compatibility")
async def check_compatibility_handler(callback: CallbackQuery):
    """Начать проверку совместимости по коду"""
    user_id = callback.from_user.id
    profile = get_user_profile(user_id)
    
    if not profile or not profile.get("completed"):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📝 Сначала пройти анкету", callback_data="start_survey")]
            ]
        )
        await callback.message.answer(
            "Сначала нужно заполнить анкету.\nПосле этого вы сможете проверять совместимость с другими.",
            reply_markup=keyboard
        )
        await callback.answer()
        return
    
    await callback.message.answer(
        "Введите код анкеты другого человека:\n\n"
        "Пример: <code>PABC123DE</code>\n\n"
        "Этот код вам должен предоставить человек, с которым вы хотите проверить совместимость.",
        parse_mode="HTML"
    )
    
    user_sessions[user_id] = {"mode": "waiting_for_profile_code"}
    await callback.answer()

@dp.callback_query(F.data == "start_survey")
async def start_survey_handler(callback: CallbackQuery):
    """Начать заполнение анкеты"""
    user_id = callback.from_user.id
    username = callback.from_user.username or ""
    first_name = callback.from_user.first_name or ""
    
    save_user_profile(user_id, username, first_name)
    
    user_sessions[user_id] = {
        "current": 0,
        "answers": {},
        "mode": "survey"
    }
    
    await send_question(user_id)
    await callback.answer()

async def send_question(user_id):
    """Отправить текущий вопрос пользователю"""
    if user_id not in user_sessions:
        return
    
    session = user_sessions[user_id]
    current_index = session["current"]
    
    if current_index >= len(questions):
        await finish_survey(user_id)
        return
    
    question = questions[current_index]
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1", callback_data="ans_1"),
                InlineKeyboardButton(text="2", callback_data="ans_2"),
                InlineKeyboardButton(text="3", callback_data="ans_3"),
                InlineKeyboardButton(text="4", callback_data="ans_4"),
                InlineKeyboardButton(text="5", callback_data="ans_5"),
                InlineKeyboardButton(text="6", callback_data="ans_6"),
                InlineKeyboardButton(text="7", callback_data="ans_7"),
            ]
        ]
    )
    
    question_text = f"Вопрос {current_index + 1}/{len(questions)}\n\n{question['text']}"
    await bot.send_message(user_id, question_text, reply_markup=keyboard)

@dp.callback_query(F.data.startswith("ans_"))
async def handle_answer(callback: CallbackQuery):
    """Обработка ответа"""
    user_id = callback.from_user.id
    
    if user_id not in user_sessions:
        await callback.answer()
        return
    
    try:
        answer = int(callback.data.split("_")[1])
        if answer < 1 or answer > 7:
            raise ValueError
    except:
        await callback.answer("Ошибка: неверный ответ")
        return
    
    session = user_sessions[user_id]
    current_index = session["current"]
    question_id = questions[current_index]["id"]
    
    session["answers"][question_id] = answer
    session["current"] += 1
    
    await callback.answer(f"Ответ {answer} сохранён")
    await send_question(user_id)

async def finish_survey(user_id):
    """Завершить анкету и сохранить результаты"""
    if user_id not in user_sessions:
        return
    
    session = user_sessions[user_id]
    answers = session["answers"]
    
    profile = get_user_profile(user_id)
    if profile:
        username = profile.get("username", "")
        first_name = profile.get("first_name", "")
    else:
        username = ""
        first_name = ""
    
    save_user_profile(user_id, username, first_name, answers, completed=True)
    updated_profile = get_user_profile(user_id)
    profile_code = updated_profile["profile_code"]
    
    completion_text = (
        f"🎉 <b>Анкета успешно завершена!</b>\n\n"
        f"🆔 Ваш уникальный код анкеты:\n<code>{profile_code}</code>\n\n"
        f"<b>Теперь вы можете:</b>\n"
        f"1. Поделиться этим кодом с другими\n"
        f"2. Проверить совместимость с чужой анкетой\n"
        f"3. Использовать код многократно"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Поделиться кодом", 
                                 url=f"https://t.me/share/url?url=Мой%20код%20анкеты%20совместимости:%20{profile_code}")],
            [InlineKeyboardButton(text="🔍 Проверить совместимость", callback_data="check_compatibility")],
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        ]
    )
    
    await bot.send_message(user_id, completion_text, reply_markup=keyboard, parse_mode="HTML")
    
    if user_id in user_sessions:
        del user_sessions[user_id]

@dp.message(F.text)
async def handle_text_message(message: Message):
    """Обработка текстовых сообщений (ввод кодов)"""
    user_id = message.from_user.id
    text = message.text.strip().upper()
    
    if user_id in user_sessions and user_sessions[user_id].get("mode") == "waiting_for_profile_code":
        other_profile = get_profile_by_code(text)
        
        if not other_profile:
            await message.answer(
                "❌ Код не найден или анкета не завершена.\n"
                "Проверьте правильность кода и попробуйте снова.\n\n"
                "Пример кода: <code>PABC123DE</code>",
                parse_mode="HTML"
            )
            return
        
        my_profile = get_user_profile(user_id)
        
        if not my_profile or not my_profile.get("completed"):
            await message.answer("Сначала заполните свою анкету.")
            return
        
        if other_profile["user_id"] == user_id:
            await message.answer("Нельзя проверить совместимость с собой же!")
            return
        
        compatibility_result = calculate_compatibility(
            my_profile["answers"], 
            other_profile["answers"]
        )
        
        # Формируем результат
        total_percent = compatibility_result["total_percent"]
        
        if total_percent >= 80:
            emoji = "💞"
            rating = "ИДЕАЛЬНАЯ СОВМЕСТИМОСТЬ"
        elif total_percent >= 60:
            emoji = "✨"
            rating = "ХОРОШАЯ СОВМЕСТИМОСТЬ"
        elif total_percent >= 40:
            emoji = "⚖️"
            rating = "СРЕДНЯЯ СОВМЕСТИМОСТЬ"
        else:
            emoji = "⚠️"
            rating = "НИЗКАЯ СОВМЕСТИМОСТЬ"
        
        result_message = (
            f"{emoji} <b>РЕЗУЛЬТАТ СОВМЕСТИМОСТИ</b>\n"
            f"С вами: {other_profile['first_name'] or 'Пользователь'}\n\n"
            f"🏆 <b>Общий показатель:</b> {total_percent}%\n"
            f"📊 <b>Уровень:</b> {rating}\n\n"
        )
        
        result_message += "<b>📈 Детальная оценка по сферам:</b>\n"
        for block_num in sorted(compatibility_result["block_percents"].keys()):
            block_data = compatibility_result["block_percents"][block_num]
            percent = block_data["percent"]
            
            if percent >= 80:
                block_emoji = "🟢"
            elif percent >= 60:
                block_emoji = "🟡"
            elif percent >= 40:
                block_emoji = "🟠"
            else:
                block_emoji = "🔴"
            
            result_message += f"{block_emoji} {block_data['name']}: {percent}%\n"
        
        result_message += "\n<b>🔮 ПРОГНОЗ И ОЖИДАНИЯ:</b>\n"
        for i, forecast in enumerate(compatibility_result["forecasts"][:3], 1):
            result_message += f"{i}. {forecast}\n"
        
        result_message += "\n<b>💡 РЕКОМЕНДАЦИИ ДЛЯ ПАРЫ:</b>\n"
        for i, recommendation in enumerate(compatibility_result["recommendations"][:3], 1):
            result_message += f"{i}. {recommendation}\n"
        
        if compatibility_result["strong_areas"]:
            result_message += "\n<b>✅ СИЛЬНЫЕ СТОРОНЫ ОТНОШЕНИЙ:</b>\n"
            for block_num, block_data in compatibility_result["strong_areas"][:2]:
                result_message += f"• {block_data['name']} ({block_data['percent']}%)\n"
        
        if compatibility_result["risk_areas"]:
            result_message += "\n<b>⚠️ ОБЛАСТИ ВНИМАНИЯ:</b>\n"
            for block_num, block_data in compatibility_result["risk_areas"][:2]:
                result_message += f"• {block_data['name']} ({block_data['percent']}%)\n"
        
        result_message += "\n<b>💭 ЗАКЛЮЧЕНИЕ:</b>\n"
        result_message += "Этот результат — инструмент для осознанного построения отношений."
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить другого", callback_data="check_compatibility")],
                [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
            ]
        )
        
        await message.answer(result_message, reply_markup=keyboard, parse_mode="HTML")
        del user_sessions[user_id]

# === ЗАПУСК БОТА ===
async def main():
    logger.info("🤖 Бот совместимости запускается...")
    logger.info("📊 Всего вопросов: %d", len(questions))
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 БОТ ДЛЯ ПРОВЕРКИ СОВМЕСТИМОСТИ ПАР")
    print("=" * 50)
    print("• Безопасная загрузка токена")
    print("• 12 вопросов по 6 сферам")
    print("• Индивидуальные коды анкет")
    print("• Проверка совместимости по коду")
    print("=" * 50)
    
    asyncio.run(main())
