# main.py
# Главный файл для запуска Telegram-бота
# Инициализирует бота, подключает обработчики и запускает планировщик

import asyncio
from datetime import datetime
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, BOT_VERSION, CHECK_INTERVAL_HOURS
from logger_setup import logger
from database import init_db, get_all_users
from handlers import router
from parser import get_deadline_events

# Проверяем наличие токена
if not BOT_TOKEN:
    logger.error("Ошибка! BOT_TOKEN не найден.")
    raise ValueError(
        "Ошибка! BOT_TOKEN не найден.\n"
        "Создайте файл .env и добавьте: BOT_TOKEN=ваш_токен_от_botfather"
    )

# Создаем экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключаем router с обработчиками команд
dp.include_router(router)


async def check_deadlines():
    """
    Фоновая задача для проверки дедлайнов.
    Запускается каждый час.
    
    Процесс:
    1. Получает список всех пользователей и их ссылки на календари
    2. Для каждого пользователя скачивает iCal-фид
    3. Проверяет, есть ли события с дедлайном за 71-72 часа
    4. Отправляет уведомление, если найдены такие события
    """
    logger.info("🔄 Проверка дедлайнов начата...")
    
    try:
        # Получаем всех пользователей
        users = await get_all_users()
        logger.info(f"📊 Всего пользователей в БД: {len(users)}")
        
        if not users:
            logger.info("ℹ️ Пользователей нет, проверка пропущена")
            return
        
        # Проходим по каждому пользователю
        for user_id, ical_url in users:
            try:
                logger.info(f"👤 Проверка календаря пользователя {user_id}...")
                
                # Получаем события с дедлайнами за 3 дня
                deadline_events = await get_deadline_events(ical_url)
                
                if deadline_events is None:
                    logger.warning(
                        f"⚠️ Не удалось загрузить календарь для пользователя {user_id}. "
                        f"Ссылка: {ical_url[:50]}..."
                    )
                    continue
                
                # Если есть события, отправляем уведомления
                if deadline_events:
                    logger.info(
                        f"📬 Найдено {len(deadline_events)} событий за 3 дня "
                        f"для пользователя {user_id}"
                    )
                    
                    for event in deadline_events:
                        try:
                            # Формируем текст уведомления
                            notification_text = (
                                f"⏰ НАПОМИНАНИЕ ОБ ДЕДЛАЙНЕ\n\n"
                                f"📌 Задание: {event['name']}\n"
                                f"⏳ Дедлайн: {event['deadline_str']}\n"
                                f"⌛ Осталось: 3 дня\n\n"
                                f"Не забудь выполнить работу вовремя! 📝"
                            )
                            
                            # Отправляем уведомление пользователю
                            await bot.send_message(user_id, notification_text)
                            logger.info(
                                f"✅ Уведомление отправлено пользователю {user_id} "
                                f"о задании '{event['name']}'"
                            )
                        
                        except Exception as e:
                            logger.error(
                                f"❌ Ошибка при отправке уведомления пользователю {user_id}: {e}"
                            )
                else:
                    logger.info(f"ℹ️ Нет событий за 3 дня для пользователя {user_id}")
            
            except Exception as e:
                logger.error(
                    f"❌ Ошибка при проверке календаря пользователя {user_id}: {e}"
                )
                continue
        
        logger.info("✅ Проверка дедлайнов завершена")
    
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при проверке дедлайнов: {e}")


async def scheduler_init():
    """
    Инициализирует и запускает планировщик APScheduler.
    Добавляет фоновую задачу проверки дедлайнов согласно конфигурации.
    """
    scheduler = AsyncIOScheduler()
    
    # Добавляем задачу проверки дедлайнов согласно интервалу из конфига
    scheduler.add_job(
        check_deadlines,
        'interval',
        hours=CHECK_INTERVAL_HOURS,
        id='check_deadlines',
        name='Проверка дедлайнов',
        replace_existing=True
    )
    
    # Запускаем планировщик
    scheduler.start()
    logger.info("🚀 Планировщик APScheduler запущен")
    logger.info(f"⏰ Фоновая задача проверки дедлайнов настроена на каждые {CHECK_INTERVAL_HOURS} час(ов)")
    
    return scheduler


async def main():
    """
    Главная функция для запуска бота.
    Инициализирует БД, планировщик и запускает диспетчер.
    """
    logger.info("=" * 60)
    logger.info(f"🤖 Canvas Deadline Assistant Bot v{BOT_VERSION} запускается...")
    logger.info("=" * 60)
    
    try:
        # Инициализируем базу данных
        logger.info("📁 Инициализация базы данных...")
        await init_db()
        logger.info("✅ База данных готова")
        
        # Инициализируем планировщик
        logger.info("⏰ Инициализация планировщика...")
        scheduler = await scheduler_init()
        
        # Запускаем функцию проверки дедлайнов один раз при старте
        # (через 10 секунд, чтобы дать боту время инициализироваться)
        scheduler.add_job(
            check_deadlines,
            'date',
            run_date=datetime.now() + timedelta(seconds=5),
            id='first_check'
        )
        
        # Пытаемся получить информацию о боте
        me = await bot.get_me()
        logger.info(f"✅ Бот @{me.username} подключен и готов к работе!")
        logger.info("=" * 60)
        logger.info("👂 Слушаю сообщения...")
        
        # Запускаем диспетчер (polling)
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        raise
    
    finally:
        # Закрываем сессию бота при завершении
        await bot.session.close()
        logger.info("🔌 Соединение с Telegram закрыто")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("✅ Бот корректно завершил работу")
