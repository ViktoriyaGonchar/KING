"""
Доменная модель Task (TaskContext)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class TaskStatus(str, Enum):
    """Статусы задачи"""

    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Типы задач"""

    LLM_GENERATION = "llm_generation"
    RAG_QUERY = "rag_query"
    DATA_PROCESSING = "data_processing"
    MULTIMODAL = "multimodal"
    CUSTOM = "custom"


@dataclass
class Task:
    """
    Доменная модель задачи
    Представляет задачу для выполнения агентом
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    type: TaskType = TaskType.CUSTOM
    status: TaskStatus = TaskStatus.CREATED
    payload: Dict[str, Any] = field(default_factory=dict)
    assigned_agent: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def assign_to(self, agent_id: str) -> None:
        """
        Назначение задачи агенту

        Args:
            agent_id: ID агента
        """
        if self.status != TaskStatus.CREATED:
            raise ValueError(f"Задачу можно назначить только в статусе CREATED, текущий: {self.status}")

        self.assigned_agent = agent_id
        self.status = TaskStatus.ASSIGNED
        self.updated_at = datetime.utcnow()

    def start(self) -> None:
        """Начало выполнения задачи"""
        if self.status not in [TaskStatus.ASSIGNED, TaskStatus.CREATED]:
            raise ValueError(f"Задачу можно начать только в статусе ASSIGNED или CREATED, текущий: {self.status}")

        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self, result: Dict[str, Any]) -> None:
        """
        Завершение задачи успешно

        Args:
            result: Результат выполнения задачи
        """
        if self.status != TaskStatus.IN_PROGRESS:
            raise ValueError(f"Задачу можно завершить только в статусе IN_PROGRESS, текущий: {self.status}")

        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def fail(self, error: str) -> None:
        """
        Завершение задачи с ошибкой

        Args:
            error: Сообщение об ошибке
        """
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """Отмена задачи"""
        if self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            raise ValueError(f"Задачу нельзя отменить в статусе {self.status}")

        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_completed(self) -> bool:
        """Проверка завершенности задачи"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование задачи в словарь"""
        return {
            "id": self.id,
            "type": self.type.value,
            "status": self.status.value,
            "payload": self.payload,
            "assigned_agent": self.assigned_agent,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Создание задачи из словаря"""
        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"])

        completed_at = None
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"])

        return cls(
            id=data.get("id", str(uuid4())),
            type=TaskType(data.get("type", TaskType.CUSTOM.value)),
            status=TaskStatus(data.get("status", TaskStatus.CREATED.value)),
            payload=data.get("payload", {}),
            assigned_agent=data.get("assigned_agent"),
            result=data.get("result"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat())),
            started_at=started_at,
            completed_at=completed_at,
        )

