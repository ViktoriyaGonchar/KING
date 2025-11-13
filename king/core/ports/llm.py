"""
Интерфейс для LLM-адаптеров
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Union, AsyncIterator
from dataclasses import dataclass


@dataclass
class Message:
    """Сообщение в диалоге"""
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: Optional[float] = None
    metadata: Optional[dict] = None


@dataclass
class LLMResponse:
    """Ответ от LLM"""
    content: str
    metadata: Optional[dict] = None
    tokens_used: Optional[int] = None
    model: Optional[str] = None


class AbstractLLMClient(ABC):
    """
    Унифицированный интерфейс для работы с LLM-провайдерами
    Все LLM-адаптеры должны реализовывать этот интерфейс
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: Optional[List[Message]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[LLMResponse, AsyncIterator[LLMResponse]]:
        """
        Генерация ответа от LLM
        
        Args:
            prompt: Текст промпта
            context: История диалога (опционально)
            stream: Если True, возвращает AsyncIterator для streaming
            **kwargs: Дополнительные параметры (temperature, max_tokens и т.д.)
        
        Returns:
            LLMResponse или AsyncIterator[LLMResponse] при stream=True
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        prompt: str,
        context: Optional[List[Message]] = None,
        **kwargs
    ) -> AsyncIterator[LLMResponse]:
        """
        Streaming-генерация ответа
        
        Args:
            prompt: Текст промпта
            context: История диалога
            **kwargs: Дополнительные параметры
        
        Yields:
            LLMResponse с частичными ответами
        """
        pass
    
    @abstractmethod
    async def get_embeddings(self, text: str) -> List[float]:
        """
        Получение embeddings для текста
        
        Args:
            text: Текст для векторизации
        
        Returns:
            Список чисел (вектор embeddings)
        """
        pass
    
    def preprocess_context(self, context: List[Message]) -> str:
        """
        Предобработка контекста для включения в промпт
        
        Args:
            context: История диалога
        
        Returns:
            Отформатированная строка контекста
        """
        if not context:
            return ""
        
        formatted = []
        for msg in context:
            formatted.append(f"{msg.role}: {msg.content}")
        
        return "\n".join(formatted)
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Проверка доступности LLM-сервиса
        
        Returns:
            True если сервис доступен, False иначе
        """
        pass

