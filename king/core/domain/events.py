"""
Базовые доменные события
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class DomainEvent:
    """
    Базовый класс для всех доменных событий
    """

    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = field(init=False)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Автоматически устанавливает event_type из имени класса"""
        if not hasattr(self, "_event_type_set"):
            self.event_type = self.__class__.__name__
            self._event_type_set = True

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование события в словарь"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate_id": self.aggregate_id,
            "metadata": self.metadata,
        }


@dataclass
class AgentCreated(DomainEvent):
    """Событие создания агента"""

    agent_id: str
    agent_name: str
    agent_type: str
    capabilities: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        self.aggregate_id = self.agent_id
        self.metadata.update(
            {
                "agent_name": self.agent_name,
                "agent_type": self.agent_type,
                "capabilities": self.capabilities,
            }
        )


@dataclass
class AgentStatusChanged(DomainEvent):
    """Событие изменения статуса агента"""

    agent_id: str
    old_status: str
    new_status: str
    reason: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.aggregate_id = self.agent_id
        self.metadata.update(
            {
                "old_status": self.old_status,
                "new_status": self.new_status,
                "reason": self.reason,
            }
        )


@dataclass
class LLMRequestInitiated(DomainEvent):
    """Событие инициации запроса к LLM"""

    request_id: str
    prompt: str
    model: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        self.aggregate_id = self.request_id
        self.metadata.update(
            {
                "prompt": self.prompt,
                "model": self.model,
                "parameters": self.parameters,
            }
        )


@dataclass
class LLMResponseReceived(DomainEvent):
    """Событие получения ответа от LLM"""

    request_id: str
    response_content: str
    tokens_used: Optional[int] = None
    model: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.aggregate_id = self.request_id
        self.metadata.update(
            {
                "response_content": self.response_content,
                "tokens_used": self.tokens_used,
                "model": self.model,
            }
        )


@dataclass
class LLMErrorOccurred(DomainEvent):
    """Событие ошибки при работе с LLM"""

    request_id: str
    error_message: str
    error_type: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.aggregate_id = self.request_id
        self.metadata.update(
            {
                "error_message": self.error_message,
                "error_type": self.error_type,
            }
        )


@dataclass
class TaskCreated(DomainEvent):
    """Событие создания задачи"""

    task_id: str
    task_type: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        self.aggregate_id = self.task_id
        self.metadata.update(
            {
                "task_type": self.task_type,
                "payload": self.payload,
            }
        )


@dataclass
class TaskAssigned(DomainEvent):
    """Событие назначения задачи агенту"""

    task_id: str
    agent_id: str

    def __post_init__(self):
        super().__post_init__()
        self.aggregate_id = self.task_id
        self.metadata.update({"agent_id": self.agent_id})


@dataclass
class TaskCompleted(DomainEvent):
    """Событие завершения задачи"""

    task_id: str
    result: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        self.aggregate_id = self.task_id
        self.metadata.update({"result": self.result})


@dataclass
class TaskFailed(DomainEvent):
    """Событие неудачного выполнения задачи"""

    task_id: str
    error_message: str
    error_type: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.aggregate_id = self.task_id
        self.metadata.update(
            {
                "error_message": self.error_message,
                "error_type": self.error_type,
            }
        )


@dataclass
class MessageReceived(DomainEvent):
    """Событие получения сообщения"""

    message_id: str
    role: str
    content: str
    conversation_id: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.aggregate_id = self.message_id
        self.metadata.update(
            {
                "role": self.role,
                "content": self.content,
                "conversation_id": self.conversation_id,
            }
        )


@dataclass
class MessageProcessed(DomainEvent):
    """Событие обработки сообщения"""

    message_id: str
    response: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.aggregate_id = self.message_id
        self.metadata.update({"response": self.response})

