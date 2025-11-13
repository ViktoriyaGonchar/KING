"""
ConfigLoader для загрузки конфигурации из YAML/JSON файлов
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from king.core.ports.config import AbstractConfigProvider

logger = logging.getLogger(__name__)


class ConfigLoader(AbstractConfigProvider):
    """
    Загрузчик конфигурации из YAML/JSON файлов
    Поддерживает вложенные ключи через точку (например, "db.host")
    """

    def __init__(self, config_path: Path, encoding: str = "utf-8"):
        """
        Инициализация загрузчика конфигурации

        Args:
            config_path: Путь к файлу конфигурации (YAML или JSON)
            encoding: Кодировка файла
        """
        self.config_path = Path(config_path)
        self.encoding = encoding
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Загрузка конфигурации из файла"""
        if not self.config_path.exists():
            logger.warning(f"Конфигурационный файл не найден: {self.config_path}")
            return

        try:
            with open(self.config_path, "r", encoding=self.encoding) as f:
                if self.config_path.suffix in [".yaml", ".yml"]:
                    self._config = yaml.safe_load(f) or {}
                elif self.config_path.suffix == ".json":
                    self._config = json.load(f) or {}
                else:
                    raise ValueError(
                        f"Неподдерживаемый формат файла: {self.config_path.suffix}"
                    )
            logger.info(f"Конфигурация загружена из {self.config_path}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке конфигурации: {e}")
            raise

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """
        Получение вложенного значения по ключу с точкой

        Args:
            data: Словарь данных
            key: Ключ (может быть вложенным, например "db.host")

        Returns:
            Значение или None
        """
        keys = key.split(".")
        value = data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None

        return value

    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения конфигурации"""
        value = self._get_nested_value(self._config, key)
        return value if value is not None else default

    def get_secret(self, key: str) -> str:
        """Получение секретного значения"""
        value = self.get(key)
        if value is None:
            raise ValueError(f"Секрет '{key}' не найден в конфигурации")
        return str(value)

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Получение булевого значения"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    def get_int(self, key: str, default: int = 0) -> int:
        """Получение целочисленного значения"""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Не удалось преобразовать '{key}' в int, используется default: {default}")
            return default

    def reload(self) -> None:
        """Перезагрузка конфигурации из файла"""
        self._load_config()

    def get_all(self) -> Dict[str, Any]:
        """Получение всей конфигурации"""
        return self._config.copy()

