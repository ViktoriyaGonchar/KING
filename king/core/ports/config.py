"""
Интерфейс для провайдеров конфигурации
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class AbstractConfigProvider(ABC):
    """
    Абстракция над провайдерами конфигурации
    (переменные окружения, файлы, Vault и т.д.)
    """
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        Получение значения конфигурации
        
        Args:
            key: Ключ конфигурации (может быть вложенным, например "db.host")
            default: Значение по умолчанию
        
        Returns:
            Значение конфигурации
        """
        pass
    
    @abstractmethod
    def get_secret(self, key: str) -> str:
        """
        Получение секретного значения (токены, пароли и т.д.)
        
        Args:
            key: Ключ секрета
        
        Returns:
            Секретное значение
        
        Raises:
            ValueError: Если секрет не найден
        """
        pass
    
    @abstractmethod
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Получение булевого значения
        
        Args:
            key: Ключ конфигурации
            default: Значение по умолчанию
        
        Returns:
            Булево значение
        """
        pass
    
    @abstractmethod
    def get_int(self, key: str, default: int = 0) -> int:
        """
        Получение целочисленного значения
        
        Args:
            key: Ключ конфигурации
            default: Значение по умолчанию
        
        Returns:
            Целочисленное значение
        """
        pass

