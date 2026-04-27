# logger_setup.py
# Конфигурация логирования для бота

import logging
from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT


def setup_logger():
    """
    Настраивает логирование для приложения.
    Логирует в файл и на консоль одновременно.
    
    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Удаляем существующие обработчики, чтобы избежать дублирования
    logger.handlers.clear()
    
    # Форматтер для логов
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Обработчик для записи в файл
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Обработчик для вывода на консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# Инициализируем логгер при импорте модуля
logger = setup_logger()
