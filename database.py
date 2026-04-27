# database.py
# Модуль для работы с базой данных SQLite
# Использует aiosqlite для асинхронных операций

import aiosqlite
from pathlib import Path
from config import DATABASE_PATH

# Используем путь из конфигурации
DB_PATH = DATABASE_PATH


async def init_db():
    """
    Инициализирует базу данных.
    Создает таблицу users, если её нет.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                ical_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def save_user_link(user_id: int, ical_url: str):
    """
    Сохраняет или обновляет ссылку на iCal-фид для пользователя.
    
    Args:
        user_id: ID пользователя в Telegram
        ical_url: URL на iCal-фид
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли уже такой пользователь
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (user_id,)
        )
        existing_user = await cursor.fetchone()
        
        if existing_user:
            # Обновляем существующую запись
            await db.execute(
                "UPDATE users SET ical_url = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (ical_url, user_id)
            )
        else:
            # Создаем новую запись
            await db.execute(
                "INSERT INTO users (user_id, ical_url) VALUES (?, ?)",
                (user_id, ical_url)
            )
        
        await db.commit()


async def get_user_link(user_id: int) -> str | None:
    """
    Получает сохраненную ссылку на iCal-фид пользователя.
    
    Args:
        user_id: ID пользователя в Telegram
        
    Returns:
        URL на iCal-фид или None, если пользователь не найден
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT ical_url FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else None


async def get_all_users() -> list[tuple]:
    """
    Получает всех пользователей с их ссылками на iCal-фиды.
    
    Returns:
        Список кортежей (user_id, ical_url)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id, ical_url FROM users")
        return await cursor.fetchall()


async def delete_user(user_id: int):
    """
    Удаляет пользователя из базы данных.
    
    Args:
        user_id: ID пользователя в Telegram
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        await db.commit()


async def user_exists(user_id: int) -> bool:
    """
    Проверяет, существует ли пользователь в базе данных.
    
    Args:
        user_id: ID пользователя в Telegram
        
    Returns:
        True, если пользователь существует, иначе False
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM users WHERE user_id = ?",
            (user_id,)
        )
        return await cursor.fetchone() is not None
