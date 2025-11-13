"""
Доменный слой (Domain Layer)
Содержит доменные модели и события
"""

from king.core.domain.agent import Agent, AgentStatus, AgentType
from king.core.domain.events import (
    AgentCreated,
    AgentStatusChanged,
    DomainEvent,
    LLMErrorOccurred,
    LLMRequestInitiated,
    LLMResponseReceived,
    MessageProcessed,
    MessageReceived,
    TaskAssigned,
    TaskCompleted,
    TaskCreated,
    TaskFailed,
)
from king.core.domain.message import Conversation, Message
from king.core.domain.task import Task, TaskStatus, TaskType

__all__ = [
    # Models
    "Agent",
    "AgentStatus",
    "AgentType",
    "Task",
    "TaskStatus",
    "TaskType",
    "Message",
    "Conversation",
    # Events
    "DomainEvent",
    "AgentCreated",
    "AgentStatusChanged",
    "LLMRequestInitiated",
    "LLMResponseReceived",
    "LLMErrorOccurred",
    "TaskCreated",
    "TaskAssigned",
    "TaskCompleted",
    "TaskFailed",
    "MessageReceived",
    "MessageProcessed",
    # Event Infrastructure
    "EventBus",
    "EventDispatcher",
]

# Импорт Event Bus после определения событий
from king.core.domain.event_bus import EventBus, EventDispatcher
