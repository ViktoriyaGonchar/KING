"""
Pydantic схемы для REST API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Agent Schemas
class AgentCreate(BaseModel):
    """Схема для создания агента"""

    name: str = Field(..., description="Имя агента")
    type: str = Field(..., description="Тип агента")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Возможности агента")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные")


class AgentResponse(BaseModel):
    """Схема ответа с информацией об агенте"""

    id: str
    name: str
    type: str
    status: str
    capabilities: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# Task Schemas
class TaskCreate(BaseModel):
    """Схема для создания задачи"""

    type: str = Field(..., description="Тип задачи")
    payload: Dict[str, Any] = Field(..., description="Данные задачи")
    priority: int = Field(default=0, description="Приоритет задачи")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Метаданные")


class TaskResponse(BaseModel):
    """Схема ответа с информацией о задаче"""

    id: str
    type: str
    status: str
    payload: Dict[str, Any]
    assigned_agent: Optional[str]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    started_at: Optional[str]
    completed_at: Optional[str]

    class Config:
        from_attributes = True


# Message Schemas
class MessageCreate(BaseModel):
    """Схема для создания сообщения"""

    content: str = Field(..., description="Содержимое сообщения")
    role: str = Field(default="user", description="Роль отправителя")
    conversation_id: Optional[str] = Field(default=None, description="ID диалога")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Метаданные")


class MessageResponse(BaseModel):
    """Схема ответа с информацией о сообщении"""

    id: str
    role: str
    content: str
    timestamp: str
    metadata: Dict[str, Any]
    conversation_id: Optional[str]

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Схема ответа с информацией о диалоге"""

    id: str
    messages: List[MessageResponse]
    context: Dict[str, Any]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# LLM Schemas
class LLMGenerateRequest(BaseModel):
    """Схема запроса на генерацию ответа"""

    prompt: str = Field(..., description="Текст промпта")
    context: Optional[List[Dict[str, str]]] = Field(default=None, description="История диалога")
    temperature: Optional[float] = Field(default=0.7, description="Температура генерации")
    max_tokens: Optional[int] = Field(default=1000, description="Максимальное количество токенов")
    stream: bool = Field(default=False, description="Streaming режим")


class LLMGenerateResponse(BaseModel):
    """Схема ответа с результатом генерации"""

    content: str
    model: Optional[str]
    tokens_used: Optional[int]
    metadata: Optional[Dict[str, Any]]


# Health Check
class HealthResponse(BaseModel):
    """Схема ответа health check"""

    status: str
    service: str
    version: str
    timestamp: str


# Error Schemas
class ErrorResponse(BaseModel):
    """Схема ответа с ошибкой"""

    error: str
    detail: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

