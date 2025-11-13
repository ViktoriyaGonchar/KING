"""
Порты (интерфейсы) для адаптеров и репозиториев
"""

from king.core.ports.config import AbstractConfigProvider
from king.core.ports.llm import AbstractLLMClient, LLMResponse, Message
from king.core.ports.messaging import AbstractEventBus, AbstractMessageQueue, Event
from king.core.ports.repositories import (
    IAgentRepository,
    IMessageRepository,
    ITaskRepository,
)
from king.core.ports.vector_store import AbstractVectorStore, SearchResult, Vector

__all__ = [
    # Config
    "AbstractConfigProvider",
    # LLM
    "AbstractLLMClient",
    "LLMResponse",
    "Message",
    # Messaging
    "AbstractMessageQueue",
    "AbstractEventBus",
    "Event",
    # Repositories
    "IAgentRepository",
    "ITaskRepository",
    "IMessageRepository",
    # Vector Store
    "AbstractVectorStore",
    "Vector",
    "SearchResult",
]
