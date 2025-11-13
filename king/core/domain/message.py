"""
Доменные модели Message и Conversation (MessageContext)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import uuid4


@dataclass
class Message:
    """
    Доменная модель сообщения
    Представляет сообщение в диалоге
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    role: str = "user"  # "system", "user", "assistant"
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)
    conversation_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Преобразование сообщения в словарь"""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "conversation_id": self.conversation_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Создание сообщения из словаря"""
        timestamp = datetime.utcnow()
        if data.get("timestamp"):
            timestamp = datetime.fromisoformat(data["timestamp"])

        return cls(
            id=data.get("id", str(uuid4())),
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
            conversation_id=data.get("conversation_id"),
        )


@dataclass
class Conversation:
    """
    Доменная модель диалога
    Представляет серию сообщений между пользователем и агентом
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    messages: List[Message] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, message: Message) -> None:
        """
        Добавление сообщения в диалог

        Args:
            message: Сообщение для добавления
        """
        message.conversation_id = self.id
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def get_messages_by_role(self, role: str) -> List[Message]:
        """
        Получение сообщений по роли

        Args:
            role: Роль сообщений ("system", "user", "assistant")

        Returns:
            Список сообщений с указанной ролью
        """
        return [msg for msg in self.messages if msg.role == role]

    def get_last_message(self) -> Optional[Message]:
        """Получение последнего сообщения"""
        return self.messages[-1] if self.messages else None

    def to_dict(self) -> dict:
        """Преобразование диалога в словарь"""
        return {
            "id": self.id,
            "messages": [msg.to_dict() for msg in self.messages],
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Conversation":
        """Создание диалога из словаря"""
        messages = [Message.from_dict(msg_data) for msg_data in data.get("messages", [])]

        created_at = datetime.utcnow()
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        updated_at = datetime.utcnow()
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            id=data.get("id", str(uuid4())),
            messages=messages,
            context=data.get("context", {}),
            created_at=created_at,
            updated_at=updated_at,
        )

