"""
Доменная модель Agent (AgentContext)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class AgentStatus(str, Enum):
    """Статусы агента"""

    CREATED = "created"
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


class AgentType(str, Enum):
    """Типы агентов"""

    LLM = "llm"
    TASK_EXECUTOR = "task_executor"
    ORCHESTRATOR = "orchestrator"
    RAG = "rag"
    MULTIMODAL = "multimodal"


@dataclass
class Agent:
    """
    Доменная модель агента
    Представляет ИИ-агента в системе
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    type: AgentType = AgentType.LLM
    status: AgentStatus = AgentStatus.CREATED
    capabilities: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def change_status(self, new_status: AgentStatus, reason: Optional[str] = None) -> None:
        """
        Изменение статуса агента

        Args:
            new_status: Новый статус
            reason: Причина изменения статуса
        """
        if self.status == new_status:
            return

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()

        # Здесь можно добавить публикацию события AgentStatusChanged
        # через event bus

    def add_capability(self, capability: str, value: Any) -> None:
        """
        Добавление возможности агенту

        Args:
            capability: Название возможности
            value: Значение возможности
        """
        self.capabilities[capability] = value
        self.updated_at = datetime.utcnow()

    def remove_capability(self, capability: str) -> None:
        """
        Удаление возможности у агента

        Args:
            capability: Название возможности
        """
        if capability in self.capabilities:
            del self.capabilities[capability]
            self.updated_at = datetime.utcnow()

    def has_capability(self, capability: str) -> bool:
        """
        Проверка наличия возможности

        Args:
            capability: Название возможности

        Returns:
            True если возможность есть, False иначе
        """
        return capability in self.capabilities

    def is_available(self) -> bool:
        """
        Проверка доступности агента для выполнения задач

        Returns:
            True если агент доступен, False иначе
        """
        return self.status in [AgentStatus.ACTIVE, AgentStatus.IDLE]

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование агента в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        """Создание агента из словаря"""
        return cls(
            id=data.get("id", str(uuid4())),
            name=data.get("name", ""),
            type=AgentType(data.get("type", AgentType.LLM.value)),
            status=AgentStatus(data.get("status", AgentStatus.CREATED.value)),
            capabilities=data.get("capabilities", {}),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat())),
        )

