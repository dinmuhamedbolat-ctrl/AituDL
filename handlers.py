# handlers.py
# Модуль с обработчиками команд Telegram-бота

from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
import logging

from config import MAX_NEXT_DEADLINES, MAX_URL_DISPLAY_LENGTH
from database import save_user_link, get_user_link, user_exists
from parser import validate_ical_url, get_next_deadlines

# Создаем router для обработки команд
router = Router()

# Настройка логирования
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение и инструкцию.
    """
    welcome_text = """
    
    🤖 Добро пожаловать в AituDL — твой личный менеджер дедлайнов!

Этот бот следит за тем, чтобы ты не пропустил задания в AITU Moodle.

📋 Что умеет бот:
• Синхронизируется с твоим календарем Moodle.
• Автоматически проверяет новые задания.
• Присылает уведомление ровно за 3 дня до дедлайна.

🔧 Команды:
/set_link [URL] - Привязать календарь Moodle
/check - Посмотреть ближайшие 5 дедлайнов
/status - Проверить статус подписки
/help - Инструкция

📝 Как получить ссылку на календарь:
1. Зайди на lms.astanait.edu.kz
2. Перейди в раздел "Календарь" (Calendar).
3. Нажми кнопку "Экспорт календаря" (Export calendar) внизу страницы.
4. Выбери "Все события" и "Недавние и следующие 60 дней".
5. Нажми "Получить URL календаря" (Get calendar URL).
6. Скопируй ссылку и отправь её мне командой: 
/set_link [твоя_ссылка]

Начнем? 👉 Просто отправь /set_link со своей ссылкой!
"""
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработчик команды /help.
    Отправляет подробную справку.
    """
    help_text = """
📖 Справка по использованию

🔗 /set_link [URL] - Сохранить ссылку на iCal-фид
Пример: /set_link https://canvas.instructure.com/feeds/calendars/user123.ics

Ссылка должна:
• Начинаться с http:// или https://
• Содержать расширение .ics

/check - Посмотреть ближайшие дедлайны
Покажет 5 ближайших дедлайнов из вашего календаря.

⏰ Как работают уведомления:
Бот проверяет календарь каждый час.
Когда до дедлайна остается ровно 3 дня (71-72 часа), 
вы получите уведомление с названием задания и точным временем.

❌ Если возникли проблемы:
• Проверьте, что ссылка правильная (/set_link)
• Убедитесь, что статус календаря "Public"
• Попробуйте повторить попытку через минуту

💡 Совет:
Используй /check, чтобы убедиться, что ссылка работает.
    """
    await message.answer(help_text)


@router.message(Command("set_link"))
async def cmd_set_link(message: Message, command: CommandObject):
    """
    Обработчик команды /set_link.
    Валидирует URL и сохраняет ссылку на iCal-фид в БД.
    """
    if not command.args:
        await message.answer(
            "❌ Ошибка: URL не указан.\n\n"
            "Использование: /set_link [URL]\n"
            "Пример: /set_link https://canvas.instructure.com/feeds/calendars/user123.ics"
        )
        return
    
    url = command.args.strip()
    
    # Валидируем URL
    if not await validate_ical_url(url):
        await message.answer(
            "❌ Ошибка валидации ссылки.\n\n"
            "Ссылка должна:\n"
            "• Начинаться с http:// или https://\n"
            "• Содержать расширение .ics\n\n"
            f"Полученная ссылка: {url}"
        )
        return
    
    try:
        # Сохраняем ссылку в БД
        user_id = message.from_user.id
        await save_user_link(user_id, url)
        
        await message.answer(
            "✅ Ссылка успешно сохранена!\n\n"
            "Бот будет проверять ваш календарь каждый час "
            "и отправлять уведомления за 3 дня до дедлайна.\n\n"
            "Используй /check, чтобы проверить ближайшие дедлайны."
        )
        logger.info(f"Пользователь {user_id} сохранил ссылку: {url}")
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении ссылки для пользователя {message.from_user.id}: {e}")
        await message.answer(
            "❌ Ошибка при сохранении ссылки.\n"
            "Пожалуйста, попробуйте позже."
        )


@router.message(Command("check"))
async def cmd_check(message: Message):
    """
    Обработчик команды /check.
    Проверяет и показывает ближайшие дедлайны пользователя.
    """
    user_id = message.from_user.id
    
    # Проверяем, есть ли сохраненная ссылка
    ical_url = await get_user_link(user_id)
    
    if not ical_url:
        await message.answer(
            "❌ У вас нет сохраненной ссылки на календарь.\n\n"
            "Используйте /set_link, чтобы добавить свой URL ИЗ Moodle."
        )
        return
    
    # Получаем ближайшие дедлайны
    await message.answer("⏳ Загружаю ваш календарь...")
    
    try:
        deadlines = await get_next_deadlines(ical_url)
        
        if deadlines is None:
            await message.answer(
                "❌ Ошибка при загрузке календаря.\n"
                "Проверьте, что ссылка правильная и календарь доступен."
            )
            return
        
        if not deadlines:
            await message.answer(
                "📭 В ближайшее время у вас нет дедлайнов.\n"
                "Хорошего дня! 😊"
            )
            return
        
        # Формируем сообщение со списком дедлайнов
        response = "📅 Ваши ближайшие дедлайны:\n\n"
        
        for i, deadline in enumerate(deadlines, 1):
            # Форматируем дату из объекта datetime
            deadline_time = deadline['dtstart'].strftime('%d.%m.%Y %H:%M') if hasattr(deadline['dtstart'], 'strftime') else str(deadline['dtstart'])
            response += (
                f"{i}. 📌 {deadline['summary']}\n"
                f"   ⏰ {deadline_time}\n\n"
            )
        
        response += "⏳ Вы получите уведомление за 3 дня до каждого дедлайна."
        
        await message.answer(response)
        logger.info(f"Пользователь {user_id} проверил дедлайны")
    
    except Exception as e:
        logger.error(f"Ошибка при проверке дедлайнов для пользователя {user_id}: {e}")
        await message.answer(
            "❌ Ошибка при загрузке календаря.\n"
            "Пожалуйста, попробуйте позже."
        )


@router.message(Command("status"))
async def cmd_status(message: Message):
    """
    Обработчик команды /status.
    Показывает статус подписки пользователя.
    """
    user_id = message.from_user.id
    
    try:
        ical_url = await get_user_link(user_id)
        
        if ical_url:
            # Скрываем полный URL для безопасности
            masked_url = ical_url[:MAX_URL_DISPLAY_LENGTH] + "..." if len(ical_url) > MAX_URL_DISPLAY_LENGTH else ical_url
            status_text = (
                "✅ Статус: Активен\n\n"
                f"🔗 Ваша ссылка: {masked_url}\n\n"
                "📬 Вы будете получать уведомления за 3 дня до дедлайна."
            )
        else:
            status_text = (
                "⏸ Статус: Не активирован\n\n"
                "Используйте /set_link, чтобы добавить свой календарь."
            )
        
        await message.answer(status_text)
    
    except Exception as e:
        logger.error(f"Ошибка при получении статуса для пользователя {user_id}: {e}")
        await message.answer("❌ Ошибка при получении статуса.")
