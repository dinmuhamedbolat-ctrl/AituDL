# parser.py
# Модуль для парсинга iCal-фидов и получения информации о дедлайнах
import httpx
from icalendar import Calendar
from datetime import datetime, timedelta
from icalevents.icalevents import events as ical_events
import logging
import pytz
from config import DEADLINE_CHECK_HOURS_START, DEADLINE_CHECK_HOURS_END

# Настройка логирования
logger = logging.getLogger(__name__)


async def validate_ical_url(url: str) -> bool:
    
    is_http = url.startswith("http")
    is_calendar = ".ics" in url or "export_execute.php" in url
    return is_http and is_calendar

def fetch_ical_events(ical_url: str) -> list[dict] | None:
    """
    Скачивает iCal-фид с указанной ссылки и парсит события.
    Использует icalevents.events для работы с URL напрямую.
    
    Функция синхронная, так как icalevents.events() выполняет 
    блокирующие операции HTTP.
    
    Args:
        ical_url: URL на iCal-фид
        
    Returns:
        Список событий с информацией о дедлайнах или None при ошибке
    """
    try:
        # Используем events() для загрузки событий непосредственно с URL
        # По умолчанию events() получает события за последние 365 дней до сегодня
        # и 365 дней в будущее
        event_list = ical_events(url=ical_url)
        
        # Преобразуем события в удобный формат
        parsed_events = []
        for event in event_list:
            parsed_events.append({
                "summary": event.summary or "Без названия",
                "start": event.start,
                "end": event.end,
                "description": event.description or "",
            })
        
        logger.info(f"✅ Успешно загружено {len(parsed_events)} событий из {ical_url[:50]}...")
        return parsed_events
    
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке/парсинге iCal-фида {ical_url}: {e}")
        return None


async def get_deadline_events(ical_url: str) -> list[dict] | None:
    """
    Получает события, у которых дедлайн наступит за 3 дня (71-72 часа).
    
    Args:
        ical_url: URL на iCal-фид
        
    Returns:
        Список событий, дедлайны которых наступают за 3 дня
    """
    import asyncio
    
    # Запускаем синхронную функцию в отдельном потоке
    events = await asyncio.to_thread(fetch_ical_events, ical_url)
    
    if events is None:
        return None
    
    # Текущее время
    now = datetime.now()
    
    # Диапазон времени для проверки согласно конфигурации
    # (чтобы уведомление пришло ровно один раз за 3 дня)
    time_check_start = now + timedelta(hours=DEADLINE_CHECK_HOURS_START)
    time_check_end = now + timedelta(hours=DEADLINE_CHECK_HOURS_END)
    
    deadline_events = []
    
    for event in events:
        # Используем дату окончания события как дедлайн
        deadline = event.get("end")
        
        if deadline and isinstance(deadline, datetime):
            # Проверяем, попадает ли дедлайн в нужный диапазон времени
            if time_check_start <= deadline <= time_check_end:
                deadline_events.append({
                    "name": event["summary"],
                    "deadline": deadline,
                    "deadline_str": deadline.strftime("%d.%m.%Y %H:%M"),
                })
        elif deadline and hasattr(deadline, 'date'):
            # Если это объект date (без времени), конвертируем в datetime
            deadline_dt = datetime.combine(deadline, datetime.min.time())
            if time_check_start <= deadline_dt <= time_check_end:
                deadline_events.append({
                    "name": event["summary"],
                    "deadline": deadline_dt,
                    "deadline_str": deadline_dt.strftime("%d.%m.%Y"),
                })
    
    return deadline_events


async def get_next_deadlines(url: str):
    """Получает следующие дедлайны из iCal-календаря с обходом блокировок LMS."""
    EXCLUDED_KEYWORDS = ["attendance", "office hour", "консультация", "meeting"]
    try:
        # Реалистичные headers для обхода блокировок сервера
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/calendar, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            if response.status_code != 200:
                logger.warning(f"⚠️ Сервер вернул статус {response.status_code} для {url[:50]}...")
                return []
            
            # Проверяем, не заблокирован ли доступ (сервер возвращает HTML вместо .ics)
            response_text = response.text.strip()
            if response_text.lower().startswith('<!doctype html') or '<html' in response_text.lower():
                print(f"⛔ БЛОКИРОВКА! Сервер LMS блокирует доступ к {url[:30]}...")
                logger.error(f"❌ Сервер вернул HTML вместо iCal-фида. Возможна блокировка бота.")
                return []
            
            # Используем библиотеку icalendar для ручного парсинга
            gcal = Calendar.from_ical(response_text)
            deadlines = []
            now = datetime.now(pytz.utc)
            threshold = now + timedelta(days=14) # Смотрим на 14 дней вперед

            for component in gcal.walk():
                if component.name == "VEVENT":
                    summary = str(component.get('summary'))
                    if any(word in summary.lower() for word in EXCLUDED_KEYWORDS):
                        continue
                    dtstart = component.get('dtstart').dt
                    
                    # Приводим к одному формату времени (с таймзоной)
                    if not isinstance(dtstart, datetime):
                        dtstart = datetime.combine(dtstart, datetime.min.time()).replace(tzinfo=pytz.utc)
                    elif dtstart.tzinfo is None:
                        dtstart = dtstart.replace(tzinfo=pytz.utc)

                    if now < dtstart < threshold:
                        deadlines.append({
                            'summary': summary,
                            'dtstart': dtstart
                        })
            
            # Сортируем по дате
            deadlines.sort(key=lambda x: x['dtstart'])
            logger.info(f"✅ Получено {len(deadlines)} дедлайнов из {url[:50]}...")
            return deadlines
    except Exception as e:
        logger.error(f"❌ Ошибка парсинга календаря: {e}")
        print(f"❌ Ошибка парсинга календаря: {e}")
        return []
