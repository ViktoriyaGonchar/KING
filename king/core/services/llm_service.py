"""
LLMService - унифицированный интерфейс для работы с LLM
"""

import logging
from typing import AsyncIterator, List, Optional

from king.core.domain.events import (
    LLMErrorOccurred,
    LLMRequestInitiated,
    LLMResponseReceived,
)
from king.core.ports.llm import AbstractLLMClient, LLMResponse, Message

logger = logging.getLogger(__name__)


class LLMService:
    """
    Сервис для работы с LLM-провайдерами
    Обеспечивает унифицированный интерфейс независимо от провайдера
    """

    def __init__(self, llm_client: AbstractLLMClient, event_bus: Optional[object] = None):
        """
        Инициализация LLM сервиса

        Args:
            llm_client: Адаптер LLM-провайдера
            event_bus: Event bus для публикации событий (опционально)
        """
        self.llm_client = llm_client
        self.event_bus = event_bus

    async def generate(
        self,
        prompt: str,
        context: Optional[List[Message]] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse | AsyncIterator[LLMResponse]:
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
        request_id = kwargs.get("request_id") or f"req_{id(prompt)}"

        try:
            # Публикация события инициации запроса
            if self.event_bus:
                event = LLMRequestInitiated(
                    request_id=request_id,
                    prompt=prompt,
                    model=kwargs.get("model"),
                    parameters=kwargs,
                )
                await self._publish_event(event)

            # Выполнение запроса
            if stream:
                return self._generate_stream(prompt, context, request_id, **kwargs)
            else:
                response = await self.llm_client.generate(prompt, context, stream=False, **kwargs)

                # Публикация события получения ответа
                if self.event_bus:
                    event = LLMResponseReceived(
                        request_id=request_id,
                        response_content=response.content,
                        tokens_used=response.tokens_used,
                        model=response.model,
                    )
                    await self._publish_event(event)

                return response

        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}", exc_info=True)

            # Публикация события ошибки
            if self.event_bus:
                event = LLMErrorOccurred(
                    request_id=request_id,
                    error_message=str(e),
                    error_type=type(e).__name__,
                )
                await self._publish_event(event)

            raise

    async def _generate_stream(
        self,
        prompt: str,
        context: Optional[List[Message]],
        request_id: str,
        **kwargs
    ) -> AsyncIterator[LLMResponse]:
        """
        Streaming-генерация ответа

        Args:
            prompt: Текст промпта
            context: История диалога
            request_id: ID запроса
            **kwargs: Дополнительные параметры

        Yields:
            LLMResponse с частичными ответами
        """
        try:
            async for chunk in self.llm_client.stream(prompt, context, **kwargs):
                yield chunk

            # Публикация события получения ответа (после завершения стрима)
            if self.event_bus:
                # Здесь можно собрать полный ответ из чанков
                event = LLMResponseReceived(
                    request_id=request_id,
                    response_content="[streaming]",
                    model=kwargs.get("model"),
                )
                await self._publish_event(event)

        except Exception as e:
            logger.error(f"Ошибка при streaming-генерации: {e}", exc_info=True)

            if self.event_bus:
                event = LLMErrorOccurred(
                    request_id=request_id,
                    error_message=str(e),
                    error_type=type(e).__name__,
                )
                await self._publish_event(event)

            raise

    async def get_embeddings(self, text: str) -> List[float]:
        """
        Получение embeddings для текста

        Args:
            text: Текст для векторизации

        Returns:
            Список чисел (вектор embeddings)
        """
        try:
            return await self.llm_client.get_embeddings(text)
        except Exception as e:
            logger.error(f"Ошибка при получении embeddings: {e}", exc_info=True)
            raise

    async def health_check(self) -> bool:
        """
        Проверка доступности LLM-сервиса

        Returns:
            True если сервис доступен, False иначе
        """
        try:
            return await self.llm_client.health_check()
        except Exception as e:
            logger.error(f"Ошибка при проверке здоровья LLM: {e}", exc_info=True)
            return False

    async def _publish_event(self, event) -> None:
        """
        Публикация события через event bus

        Args:
            event: Доменное событие
        """
        if self.event_bus and hasattr(self.event_bus, "publish"):
            try:
                await self.event_bus.publish(event)
            except Exception as e:
                logger.warning(f"Не удалось опубликовать событие: {e}")

