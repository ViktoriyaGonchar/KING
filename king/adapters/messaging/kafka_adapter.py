"""
Kafka адаптер для messaging
"""

import asyncio
import json
import logging
from typing import AsyncIterator, Callable, Dict, List, Optional

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
    from aiokafka.admin import AIOKafkaAdminClient, NewTopic
    AIOKAFKA_AVAILABLE = True
except ImportError:
    # Fallback на синхронный kafka-python
    from kafka import KafkaConsumer, KafkaProducer
    from kafka.admin import KafkaAdminClient, NewTopic
    from kafka.errors import KafkaError
    AIOKAFKA_AVAILABLE = False

from king.core.ports.messaging import AbstractMessageQueue

logger = logging.getLogger(__name__)


class KafkaAdapter(AbstractMessageQueue):
    """
    Адаптер для Apache Kafka
    Реализует интерфейс AbstractMessageQueue
    """

    def __init__(
        self,
        bootstrap_servers: str | List[str] = "localhost:9092",
        topic_prefix: str = "king",
        consumer_group: Optional[str] = None,
    ):
        """
        Инициализация Kafka адаптера

        Args:
            bootstrap_servers: Список Kafka брокеров
            topic_prefix: Префикс для топиков
            consumer_group: ID группы потребителей
        """
        if isinstance(bootstrap_servers, str):
            bootstrap_servers = [bootstrap_servers]

        self.bootstrap_servers = bootstrap_servers
        self.topic_prefix = topic_prefix
        self.consumer_group = consumer_group or f"{topic_prefix}-consumer-group"

        if AIOKAFKA_AVAILABLE:
            self._producer: Optional[AIOKafkaProducer] = None
            self._consumers: Dict[str, AIOKafkaConsumer] = {}
        else:
            self._producer = None
            self._consumers: Dict[str, KafkaConsumer] = {}

    def _get_topic_name(self, topic: str) -> str:
        """
        Получение полного имени топика с префиксом

        Args:
            topic: Имя топика

        Returns:
            Полное имя топика
        """
        if topic.startswith(self.topic_prefix):
            return topic
        return f"{self.topic_prefix}.{topic}"

    async def publish(self, topic: str, message: dict) -> None:
        """
        Публикация сообщения в топик

        Args:
            topic: Название топика
            message: Данные сообщения
        """
        topic_name = self._get_topic_name(topic)

        if AIOKAFKA_AVAILABLE:
            # Асинхронная версия с aiokafka
            if not self._producer:
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=",".join(self.bootstrap_servers),
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    acks="all",
                    retries=3,
                )
                await self._producer.start()

            try:
                record_metadata = await self._producer.send_and_wait(topic_name, message)
                logger.debug(
                    f"Сообщение опубликовано в топик {topic_name}, partition {record_metadata.partition}, offset {record_metadata.offset}"
                )
            except Exception as e:
                logger.error(f"Ошибка при публикации сообщения в Kafka: {e}", exc_info=True)
                raise
        else:
            # Синхронная версия с kafka-python (запускаем в executor)
            loop = asyncio.get_event_loop()
            if not self._producer:
                self._producer = await loop.run_in_executor(
                    None,
                    lambda: KafkaProducer(
                        bootstrap_servers=self.bootstrap_servers,
                        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                        acks="all",
                        retries=3,
                    ),
                )

            try:
                future = self._producer.send(topic_name, message)
                record_metadata = await loop.run_in_executor(None, lambda: future.get(timeout=10))
                logger.debug(
                    f"Сообщение опубликовано в топик {topic_name}, partition {record_metadata.partition}, offset {record_metadata.offset}"
                )
            except Exception as e:
                logger.error(f"Ошибка при публикации сообщения в Kafka: {e}", exc_info=True)
                raise

    async def subscribe(
        self,
        topic: str,
        handler: Callable[[dict], None],
        group_id: Optional[str] = None,
    ) -> None:
        """
        Подписка на топик

        Args:
            topic: Название топика
            handler: Функция-обработчик сообщений
            group_id: ID группы потребителей
        """
        topic_name = self._get_topic_name(topic)
        consumer_group = group_id or self.consumer_group

        # Создание consumer если еще не создан
        if topic_name not in self._consumers:
            consumer = KafkaConsumer(
                topic_name,
                bootstrap_servers=self.bootstrap_servers,
                group_id=consumer_group,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            self._consumers[topic_name] = consumer
            logger.info(f"Подписка на топик {topic_name} с группой {consumer_group}")

        # Запуск обработки в фоне (в реальном приложении это должно быть через asyncio)
        # Здесь упрощенная версия - в production нужен отдельный worker
        logger.warning(
            "Kafka subscribe требует отдельного worker процесса для обработки сообщений"
        )

    async def consume(
        self,
        topic: str,
        group_id: Optional[str] = None,
    ) -> AsyncIterator[dict]:
        """
        Потребление сообщений из топика

        Args:
            topic: Название топика
            group_id: ID группы потребителей

        Yields:
            Сообщения из топика
        """
        topic_name = self._get_topic_name(topic)
        consumer_group = group_id or self.consumer_group

        if AIOKAFKA_AVAILABLE:
            # Асинхронная версия с aiokafka
            consumer = AIOKafkaConsumer(
                topic_name,
                bootstrap_servers=",".join(self.bootstrap_servers),
                group_id=consumer_group,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            await consumer.start()

            try:
                async for message in consumer:
                    yield message.value
            except Exception as e:
                logger.error(f"Ошибка при потреблении сообщений из Kafka: {e}", exc_info=True)
                raise
            finally:
                await consumer.stop()
        else:
            # Синхронная версия (упрощенная)
            logger.warning("Используется синхронный Kafka consumer, рекомендуется aiokafka")
            loop = asyncio.get_event_loop()
            consumer = await loop.run_in_executor(
                None,
                lambda: KafkaConsumer(
                    topic_name,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=consumer_group,
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    auto_offset_reset="earliest",
                    enable_auto_commit=True,
                ),
            )

            try:
                while True:
                    messages = await loop.run_in_executor(
                        None, lambda: list(consumer.poll(timeout_ms=1000).values())
                    )
                    for message_batch in messages:
                        for message in message_batch:
                            yield message.value
                    await asyncio.sleep(0.1)  # Небольшая задержка
            except Exception as e:
                logger.error(f"Ошибка при потреблении сообщений из Kafka: {e}", exc_info=True)
                raise
            finally:
                await loop.run_in_executor(None, consumer.close)

    async def create_topic(self, topic: str, num_partitions: int = 1, replication_factor: int = 1) -> None:
        """
        Создание топика (если не существует)

        Args:
            topic: Название топика
            num_partitions: Количество партиций
            replication_factor: Фактор репликации
        """
        topic_name = self._get_topic_name(topic)

        try:
            admin_client = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            topic_list = [NewTopic(name=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)]
            admin_client.create_topics(new_topics=topic_list, validate_only=False)
            logger.info(f"Топик {topic_name} создан")
        except Exception as e:
            # Топик может уже существовать
            logger.debug(f"Топик {topic_name} уже существует или ошибка создания: {e}")

    async def close(self) -> None:
        """Закрытие соединений"""
        if self._producer:
            if AIOKAFKA_AVAILABLE:
                await self._producer.stop()
            else:
                self._producer.close()
            self._producer = None

        for consumer in self._consumers.values():
            if AIOKAFKA_AVAILABLE:
                await consumer.stop()
            else:
                consumer.close()
        self._consumers.clear()

        logger.info("Kafka адаптер закрыт")

