"""
EnvironmentConfig для загрузки конфигурации из переменных окружения
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

from king.core.ports.config import AbstractConfigProvider

logger = logging.getLogger(__name__)


class EnvironmentConfig(AbstractConfigProvider):
    """
    Провайдер конфигурации из переменных окружения
    Поддерживает .env файлы и вложенные ключи через двойное подчеркивание
    (например, DB__HOST для "db.host")
    """

    def __init__(self, env_file: Optional[Path] = None, override: bool = False):
        """
        Инициализация провайдера конфигурации из переменных окружения

        Args:
            env_file: Путь к .env файлу (опционально)
            override: Если True, значения из .env перезаписывают существующие
        """
        if env_file:
            env_path = Path(env_file)
            if env_path.exists():
                load_dotenv(env_path, override=override)
                logger.info(f"Переменные окружения загружены из {env_path}")
            else:
                logger.warning(f"Файл .env не найден: {env_path}")
        else:
            # Попытка загрузить .env из корня проекта
            default_env = Path.cwd() / ".env"
            if default_env.exists():
                load_dotenv(default_env, override=override)
                logger.info(f"Переменные окружения загружены из {default_env}")

    def _normalize_key(self, key: str) -> str:
        """
        Нормализация ключа для переменных окружения
        Преобразует "db.host" в "DB__HOST" или "DB_HOST"

        Args:
            key: Ключ конфигурации

        Returns:
            Нормализованный ключ для переменной окружения
        """
        # Заменяем точку на двойное подчеркивание и приводим к верхнему регистру
        return key.replace(".", "__").upper()

    def _denormalize_key(self, env_key: str) -> str:
        """
        Обратное преобразование ключа из переменной окружения
        Преобразует "DB__HOST" в "db.host"

        Args:
            env_key: Ключ переменной окружения

        Returns:
            Денормализованный ключ
        """
        return env_key.replace("__", ".").lower()

    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения из переменных окружения"""
        env_key = self._normalize_key(key)
        value = os.getenv(env_key, default)
        return value

    def get_secret(self, key: str) -> str:
        """Получение секретного значения"""
        value = self.get(key)
        if value is None:
            raise ValueError(f"Секрет '{key}' не найден в переменных окружения")
        return str(value)

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Получение булевого значения"""
        value = self.get(key)
        if value is None:
            return default

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on", "enabled")

        return bool(value)

    def get_int(self, key: str, default: int = 0) -> int:
        """Получение целочисленного значения"""
        value = self.get(key)
        if value is None:
            return default

        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(
                f"Не удалось преобразовать '{key}' в int, используется default: {default}"
            )
            return default

    def get_all(self) -> dict:
        """Получение всех переменных окружения, связанных с проектом"""
        # Фильтруем переменные окружения по префиксу (опционально)
        # Для простоты возвращаем все, но можно добавить фильтрацию
        return dict(os.environ)

