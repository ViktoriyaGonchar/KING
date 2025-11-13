"""
Настройка логирования для платформы KING
"""

import json
import logging
import sys
from typing import Optional

from king.infrastructure.config import get_settings


def setup_logging(
    log_level: Optional[str] = None,
    json_format: bool = False,
    enable_trace_id: bool = True,
) -> None:
    """
    Настройка логирования для приложения

    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Если True, логи в формате JSON
        enable_trace_id: Если True, добавляет trace_id в логи
    """
    try:
        settings = get_settings()
        if not log_level:
            log_level = settings.app.log_level
    except Exception:
        log_level = log_level or "INFO"

    # Преобразование строки в уровень логирования
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Настройка форматтера
    if json_format:
        formatter = JSONFormatter(enable_trace_id=enable_trace_id)
    else:
        formatter = StructuredFormatter(enable_trace_id=enable_trace_id)

    # Настройка root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Удаление существующих handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Создание console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Настройка уровней для сторонних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


class StructuredFormatter(logging.Formatter):
    """Структурированный форматтер для логов"""

    def __init__(self, enable_trace_id: bool = True):
        """
        Инициализация форматтера

        Args:
            enable_trace_id: Добавлять trace_id в логи
        """
        super().__init__()
        self.enable_trace_id = enable_trace_id

    def format(self, record: logging.LogRecord) -> str:
        """Форматирование записи лога"""
        # Базовое форматирование
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Добавление trace_id если доступен
        if self.enable_trace_id and hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id

        # Добавление исключений
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Добавление дополнительных полей
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Форматирование в читаемый вид
        parts = [
            f"[{log_data['timestamp']}]",
            f"{log_data['level']:8s}",
            f"{log_data['logger']:30s}",
            f"- {log_data['message']}",
        ]

        if "trace_id" in log_data:
            parts.insert(1, f"trace_id={log_data['trace_id']}")

        return " ".join(parts)


class JSONFormatter(logging.Formatter):
    """JSON форматтер для логов (для production)"""

    def __init__(self, enable_trace_id: bool = True):
        """
        Инициализация JSON форматтера

        Args:
            enable_trace_id: Добавлять trace_id в логи
        """
        super().__init__()
        self.enable_trace_id = enable_trace_id

    def format(self, record: logging.LogRecord) -> str:
        """Форматирование записи лога в JSON"""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Добавление trace_id
        if self.enable_trace_id and hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id

        # Добавление исключений
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Добавление дополнительных полей
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """
    Получение логгера с указанным именем

    Args:
        name: Имя логгера

    Returns:
        Настроенный логгер
    """
    return logging.getLogger(name)

