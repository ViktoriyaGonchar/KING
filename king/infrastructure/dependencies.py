"""
Dependency injection для FastAPI
"""

import logging
from typing import Optional

from fastapi import Depends

from king.core.domain import EventBus
from king.core.ports.llm import AbstractLLMClient
from king.core.ports.messaging import AbstractMessageQueue
from king.core.ports.repositories import (
    IAgentRepository,
    IMessageRepository,
    ITaskRepository,
)
from king.core.services import (
    AgentOrchestrator,
    LLMService,
    MessageProcessor,
    TaskScheduler,
)
from king.infrastructure.config import get_settings, init_settings, Settings
from king.infrastructure.persistence.in_memory_repositories import (
    InMemoryAgentRepository,
    InMemoryMessageRepository,
    InMemoryTaskRepository,
)

logger = logging.getLogger(__name__)

# Глобальные экземпляры (будут инициализированы при старте)
_settings: Optional[Settings] = None
_llm_client: Optional[AbstractLLMClient] = None
_agent_repository: Optional[IAgentRepository] = None
_task_repository: Optional[ITaskRepository] = None
_message_repository: Optional[IMessageRepository] = None
_event_bus: Optional[EventBus] = None
_llm_service: Optional[LLMService] = None
_agent_orchestrator: Optional[AgentOrchestrator] = None
_task_scheduler: Optional[TaskScheduler] = None
_message_processor: Optional[MessageProcessor] = None
_message_queue: Optional[AbstractMessageQueue] = None


def init_dependencies(config_path: Optional[str] = None) -> None:
    """
    Инициализация всех зависимостей

    Args:
        config_path: Путь к файлу конфигурации (опционально)
    """
    global _settings, _llm_client, _agent_repository, _task_repository
    global _message_repository, _event_bus, _llm_service
    global _agent_orchestrator, _task_scheduler, _message_processor
    global _message_queue

    from pathlib import Path

    # Инициализация настроек
    if config_path:
        _settings = init_settings(Path(config_path))
    else:
        _settings = init_settings()

    # Инициализация репозиториев (in-memory для начала)
    _agent_repository = InMemoryAgentRepository()
    _task_repository = InMemoryTaskRepository()
    _message_repository = InMemoryMessageRepository()

    # Инициализация Event Bus
    _event_bus = EventBus()

    # Инициализация LLM клиента (GigaChat)
    if _settings.gigachat:
        try:
            from king.adapters.llm.gigachat import GigaChatAdapter

            _llm_client = GigaChatAdapter(
                client_id=_settings.gigachat.client_id,
                client_secret=_settings.gigachat.client_secret,
                base_url=_settings.gigachat.base_url,
                scope=_settings.gigachat.scope,
            )
            logger.info("GigaChat адаптер инициализирован")
        except Exception as e:
            logger.warning(f"Не удалось инициализировать GigaChat адаптер: {e}")
            _llm_client = None
    else:
        logger.warning("GigaChat настройки не найдены, LLM сервис недоступен")
        _llm_client = None

    # Инициализация сервисов
    if _llm_client:
        _llm_service = LLMService(_llm_client, event_bus=_event_bus)
    else:
        _llm_service = None
        logger.warning("LLM сервис не инициализирован (нет LLM клиента)")

    _agent_orchestrator = AgentOrchestrator(
        agent_repository=_agent_repository,
        task_repository=_task_repository,
        event_bus=_event_bus,
    )

    _task_scheduler = TaskScheduler(
        task_repository=_task_repository,
        agent_repository=_agent_repository,
        agent_orchestrator=_agent_orchestrator,
        event_bus=_event_bus,
    )

    _message_processor = MessageProcessor(
        message_repository=_message_repository,
        llm_service=_llm_service,
        event_bus=_event_bus,
    )

    # Инициализация messaging адаптеров (Kafka или RabbitMQ)
    _message_queue = None
    if _settings.kafka:
        try:
            from king.adapters.messaging.kafka_adapter import KafkaAdapter

            _message_queue = KafkaAdapter(
                bootstrap_servers=_settings.kafka.bootstrap_servers,
                topic_prefix=_settings.kafka.topic_prefix,
                consumer_group=_settings.kafka.consumer_group,
            )
            logger.info("Kafka адаптер инициализирован")
        except Exception as e:
            logger.warning(f"Не удалось инициализировать Kafka адаптер: {e}")

    # Если Kafka не настроен, можно использовать RabbitMQ (если настроен)
    # Примечание: В текущей версии Settings нет RabbitMQ настроек,
    # но можно добавить позже или использовать значения по умолчанию
    if not _message_queue:
        # Можно добавить инициализацию RabbitMQ здесь, если нужно
        logger.info("Messaging адаптер не инициализирован (Kafka не настроен)")

    logger.info("Все зависимости инициализированы")


def get_settings_dep() -> Settings:
    """Dependency для получения настроек"""
    if _settings is None:
        raise RuntimeError("Настройки не инициализированы")
    return _settings


def get_agent_repository() -> IAgentRepository:
    """Dependency для получения репозитория агентов"""
    if _agent_repository is None:
        raise RuntimeError("Репозиторий агентов не инициализирован")
    return _agent_repository


def get_task_repository() -> ITaskRepository:
    """Dependency для получения репозитория задач"""
    if _task_repository is None:
        raise RuntimeError("Репозиторий задач не инициализирован")
    return _task_repository


def get_message_repository() -> IMessageRepository:
    """Dependency для получения репозитория сообщений"""
    if _message_repository is None:
        raise RuntimeError("Репозиторий сообщений не инициализирован")
    return _message_repository


def get_llm_service() -> Optional[LLMService]:
    """Dependency для получения LLM сервиса"""
    return _llm_service


def get_agent_orchestrator() -> AgentOrchestrator:
    """Dependency для получения оркестратора агентов"""
    if _agent_orchestrator is None:
        raise RuntimeError("Оркестратор агентов не инициализирован")
    return _agent_orchestrator


def get_task_scheduler() -> TaskScheduler:
    """Dependency для получения планировщика задач"""
    if _task_scheduler is None:
        raise RuntimeError("Планировщик задач не инициализирован")
    return _task_scheduler


def get_message_processor() -> Optional[MessageProcessor]:
    """Dependency для получения процессора сообщений"""
    return _message_processor


def get_message_queue() -> Optional[AbstractMessageQueue]:
    """Dependency для получения messaging адаптера"""
    return _message_queue


async def cleanup_dependencies() -> None:
    """Очистка ресурсов при завершении"""
    global _llm_client, _event_bus, _message_queue

    # Остановка EventBus (graceful shutdown)
    if _event_bus:
        await _event_bus.stop()
        logger.info("EventBus остановлен")

    # Закрытие messaging адаптера
    if _message_queue and hasattr(_message_queue, "close"):
        await _message_queue.close()
        logger.info("Messaging адаптер закрыт")

    # Закрытие LLM клиента
    if _llm_client and hasattr(_llm_client, "close"):
        await _llm_client.close()
        logger.info("LLM клиент закрыт")

