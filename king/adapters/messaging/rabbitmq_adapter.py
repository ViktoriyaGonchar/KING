"""
RabbitMQ адаптер для messaging
"""

import json
import logging
from typing import AsyncIterator, Callable, Dict, Optional

import aio_pika
from aio_pika import Connection, Exchange, Message, Queue
from aio_pika.abc import AbstractIncomingMessage

from king.core.ports.messaging import AbstractMessageQueue

logger = logging.getLogger(__name__)


class RabbitMQAdapter(AbstractMessageQueue):
    """
    Адаптер для RabbitMQ
    Реализует интерфейс AbstractMessageQueue
    """

    def __init__(
        self,
        url: str = "amqp://guest:guest@localhost:5672/",
        exchange_name: str = "king",
        exchange_type: str = "topic",
    ):
        """
        Инициализация RabbitMQ адаптера

        Args:
            url: URL подключения к RabbitMQ
            exchange_name: Название exchange
            exchange_type: Тип exchange (direct, topic, fanout)
        """
        self.url = url
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type

        self._connection: Optional[Connection] = None
        self._exchange: Optional[Exchange] = None
        self._queues: Dict[str, Queue] = {}

    async def _ensure_connection(self) -> None:
        """Обеспечение наличия соединения"""
        if not self._connection or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(self.url)
            channel = await self._connection.channel()
            self._exchange = await channel.declare_exchange(
                self.exchange_name, type=self.exchange_type, durable=True
            )
            logger.info(f"Подключение к RabbitMQ установлено, exchange: {self.exchange_name}")

    async def publish(self, topic: str, message: dict) -> None:
        """
        Публикация сообщения в exchange

        Args:
            topic: Routing key (используется как routing key)
            message: Данные сообщения
        """
        await self._ensure_connection()

        # Сериализация сообщения
        message_body = json.dumps(message).encode("utf-8")
        rabbitmq_message = Message(message_body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT)

        try:
            await self._exchange.publish(rabbitmq_message, routing_key=topic)
            logger.debug(f"Сообщение опубликовано в exchange {self.exchange_name} с routing key {topic}")
        except Exception as e:
            logger.error(f"Ошибка при публикации сообщения в RabbitMQ: {e}", exc_info=True)
            raise

    async def subscribe(
        self,
        topic: str,
        handler: Callable[[dict], None],
        group_id: Optional[str] = None,
    ) -> None:
        """
        Подписка на очередь

        Args:
            topic: Routing key для подписки
            handler: Функция-обработчик сообщений
            group_id: ID группы потребителей (используется как имя очереди)
        """
        await self._ensure_connection()

        # Имя очереди
        queue_name = group_id or f"{self.exchange_name}.{topic}"

        # Создание очереди если еще не создана
        if queue_name not in self._queues:
            channel = await self._connection.channel()
            queue = await channel.declare_queue(queue_name, durable=True)
            await queue.bind(self._exchange, routing_key=topic)
            self._queues[queue_name] = queue
            logger.info(f"Подписка на очередь {queue_name} с routing key {topic}")

        # Запуск обработки (в реальном приложении это должно быть через asyncio task)
        logger.warning(
            "RabbitMQ subscribe требует отдельного asyncio task для обработки сообщений"
        )

    async def consume(
        self,
        topic: str,
        group_id: Optional[str] = None,
    ) -> AsyncIterator[dict]:
        """
        Потребление сообщений из очереди

        Args:
            topic: Routing key
            group_id: ID группы потребителей (имя очереди)

        Yields:
            Сообщения из очереди
        """
        await self._ensure_connection()

        queue_name = group_id or f"{self.exchange_name}.{topic}"

        # Создание очереди если не существует
        if queue_name not in self._queues:
            channel = await self._connection.channel()
            queue = await channel.declare_queue(queue_name, durable=True)
            await queue.bind(self._exchange, routing_key=topic)
            self._queues[queue_name] = queue

        queue = self._queues[queue_name]

        try:
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            data = json.loads(message.body.decode("utf-8"))
                            yield data
                        except Exception as e:
                            logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)
                            # Сообщение будет отправлено в dead letter queue или отброшено
        except Exception as e:
            logger.error(f"Ошибка при потреблении сообщений из RabbitMQ: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Закрытие соединений"""
        for queue in self._queues.values():
            # Очереди закроются вместе с каналом
            pass
        self._queues.clear()

        if self._exchange:
            # Exchange закроется вместе с каналом
            self._exchange = None

        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("RabbitMQ адаптер закрыт")

