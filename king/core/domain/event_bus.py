"""
Event Bus для доменных событий
Обеспечивает публикацию и подписку на события
"""

import asyncio
import logging
from collections import defaultdict
from typing import Callable, Dict, List, Optional

from king.core.domain.events import DomainEvent

logger = logging.getLogger(__name__)


class EventBus:
    """
    Простой Event Bus для синхронной и асинхронной обработки событий
    """

    def __init__(self):
        """Инициализация Event Bus"""
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._async_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processing = False
        self._processing_task: Optional[asyncio.Task] = None

    async def publish(self, event: DomainEvent) -> None:
        """
        Публикация события

        Args:
            event: Доменное событие
        """
        event_type = event.event_type

        # Синхронная обработка
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Ошибка в обработчике события {event_type}: {e}", exc_info=True)

        # Асинхронная обработка через очередь
        if event_type in self._async_handlers:
            await self._event_queue.put(event)

    async def subscribe(
        self, event_type: str, handler: Callable, async_processing: bool = False
    ) -> None:
        """
        Подписка на тип событий

        Args:
            event_type: Тип события (имя класса события)
            handler: Функция-обработчик
            async_processing: Если True, обработка через очередь
        """
        if async_processing:
            self._async_handlers[event_type].append(handler)
            logger.info(f"Добавлен асинхронный обработчик для {event_type}")
        else:
            self._handlers[event_type].append(handler)
            logger.info(f"Добавлен синхронный обработчик для {event_type}")

        # Запуск обработки очереди, если еще не запущена
        if async_processing and not self._processing:
            self._processing_task = asyncio.create_task(self._process_event_queue())

    async def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        Отписка от типа событий

        Args:
            event_type: Тип события
            handler: Функция-обработчик для удаления
        """
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.info(f"Удален синхронный обработчик для {event_type}")

        if handler in self._async_handlers[event_type]:
            self._async_handlers[event_type].remove(handler)
            logger.info(f"Удален асинхронный обработчик для {event_type}")

    async def _process_event_queue(self) -> None:
        """Обработка очереди событий"""
        self._processing = True
        logger.info("Запущена обработка очереди событий")

        while True:
            try:
                event = await self._event_queue.get()

                event_type = event.event_type
                if event_type in self._async_handlers:
                    for handler in self._async_handlers[event_type]:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(event)
                            else:
                                handler(event)
                        except Exception as e:
                            logger.error(
                                f"Ошибка в асинхронном обработчике события {event_type}: {e}",
                                exc_info=True,
                            )

                self._event_queue.task_done()

            except asyncio.CancelledError:
                logger.info("Обработка очереди событий остановлена")
                break
            except Exception as e:
                logger.error(f"Ошибка при обработке очереди событий: {e}", exc_info=True)

    def get_subscribed_events(self) -> List[str]:
        """
        Получение списка типов событий с подписками

        Returns:
            Список типов событий
        """
        all_events = set(self._handlers.keys()) | set(self._async_handlers.keys())
        return list(all_events)

    def get_handlers_count(self, event_type: str) -> int:
        """
        Получение количества обработчиков для типа события

        Args:
            event_type: Тип события

        Returns:
            Количество обработчиков
        """
        sync_count = len(self._handlers.get(event_type, []))
        async_count = len(self._async_handlers.get(event_type, []))
        return sync_count + async_count

    async def stop(self) -> None:
        """
        Остановка обработки событий (graceful shutdown)
        Ожидает завершения обработки всех событий в очереди
        """
        if not self._processing:
            return

        logger.info("Остановка EventBus...")
        self._processing = False

        # Отменяем задачу обработки
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

        # Ожидаем завершения обработки всех событий в очереди
        if not self._event_queue.empty():
            logger.info(f"Ожидание обработки {self._event_queue.qsize()} событий в очереди...")
            await self._event_queue.join()

        logger.info("EventBus остановлен")


class EventDispatcher:
    """
    Синхронный диспетчер событий
    Для простых случаев без асинхронности
    """

    def __init__(self):
        """Инициализация диспетчера"""
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)

    def publish(self, event: DomainEvent) -> None:
        """
        Публикация события

        Args:
            event: Доменное событие
        """
        event_type = event.event_type

        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Ошибка в обработчике события {event_type}: {e}", exc_info=True)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Подписка на тип событий

        Args:
            event_type: Тип события
            handler: Функция-обработчик
        """
        self._handlers[event_type].append(handler)
        logger.info(f"Добавлен обработчик для {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        Отписка от типа событий

        Args:
            event_type: Тип события
            handler: Функция-обработчик для удаления
        """
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.info(f"Удален обработчик для {event_type}")

