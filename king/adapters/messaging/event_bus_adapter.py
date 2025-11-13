"""
Адаптер Event Bus для messaging систем
Интегрирует доменный EventBus с внешними messaging системами
"""

import asyncio
import logging
from typing import Callable, Optional

from king.core.domain import DomainEvent, EventBus
from king.core.ports.messaging import AbstractMessageQueue

logger = logging.getLogger(__name__)


class MessagingEventBusAdapter:
    """
    Адаптер для интеграции доменного EventBus с внешними messaging системами
    Публикует доменные события в Kafka/RabbitMQ
    """

    def __init__(
        self,
        event_bus: EventBus,
        message_queue: AbstractMessageQueue,
        topic_prefix: str = "king.events",
    ):
        """
        Инициализация адаптера

        Args:
            event_bus: Доменный EventBus
            message_queue: Адаптер messaging системы
            topic_prefix: Префикс для топиков событий
        """
        self.event_bus = event_bus
        self.message_queue = message_queue
        self.topic_prefix = topic_prefix
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Запуск адаптера"""
        if self._running:
            return

        self._running = True

        # Подписка на все события доменного EventBus
        # В реальной реализации нужно подписаться на все типы событий
        logger.info("MessagingEventBusAdapter запущен")

    async def stop(self) -> None:
        """Остановка адаптера"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def publish_event(self, event: DomainEvent) -> None:
        """
        Публикация доменного события в messaging систему

        Args:
            event: Доменное событие
        """
        try:
            topic = f"{self.topic_prefix}.{event.event_type.lower()}"
            message = event.to_dict()

            await self.message_queue.publish(topic, message)
            logger.debug(f"Событие {event.event_type} опубликовано в {topic}")
        except Exception as e:
            logger.error(f"Ошибка при публикации события в messaging: {e}", exc_info=True)

    async def subscribe_to_external_events(
        self, event_type: str, handler: Callable
    ) -> None:
        """
        Подписка на внешние события из messaging системы

        Args:
            event_type: Тип события
            handler: Обработчик события
        """
        topic = f"{self.topic_prefix}.{event_type.lower()}"

        async def message_handler(message: dict):
            try:
                # Преобразование сообщения в доменное событие
                # В реальной реализации нужна десериализация
                await handler(message)
            except Exception as e:
                logger.error(f"Ошибка при обработке внешнего события: {e}", exc_info=True)

        await self.message_queue.subscribe(topic, message_handler)

