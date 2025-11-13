"""
Интерфейсы для messaging-систем (Kafka, RabbitMQ и т.д.)
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, AsyncIterator, Optional
from dataclasses import dataclass


@dataclass
class Event:
    """Доменное событие"""
    event_type: str
    payload: dict
    timestamp: float
    correlation_id: Optional[str] = None


class AbstractMessageQueue(ABC):
    """
    Абстракция над очередями сообщений (Kafka, RabbitMQ)
    """
    
    @abstractmethod
    async def publish(self, topic: str, message: dict) -> None:
        """
        Публикация сообщения в топик
        
        Args:
            topic: Название топика
            message: Данные сообщения (будут сериализованы в JSON)
        """
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        handler: Callable[[dict], None],
        group_id: Optional[str] = None
    ) -> None:
        """
        Подписка на топик
        
        Args:
            topic: Название топика
            handler: Функция-обработчик сообщений
            group_id: ID группы потребителей (для балансировки нагрузки)
        """
        pass
    
    @abstractmethod
    async def consume(
        self,
        topic: str,
        group_id: Optional[str] = None
    ) -> AsyncIterator[dict]:
        """
        Потребление сообщений из топика
        
        Args:
            topic: Название топика
            group_id: ID группы потребителей
        
        Yields:
            Сообщения из топика
        """
        pass


class AbstractEventBus(ABC):
    """
    Абстракция над event bus для доменных событий
    """
    
    @abstractmethod
    async def publish(self, event: Event) -> None:
        """
        Публикация доменного события
        
        Args:
            event: Доменное событие
        """
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], None]
    ) -> None:
        """
        Подписка на тип событий
        
        Args:
            event_type: Тип события (например, "agent.created")
            handler: Функция-обработчик события
        """
        pass
    
    @abstractmethod
    async def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Event], None]
    ) -> None:
        """
        Отписка от типа событий
        
        Args:
            event_type: Тип события
            handler: Функция-обработчик для удаления
        """
        pass

