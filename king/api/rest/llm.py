"""
REST API endpoints для работы с LLM
"""

import logging
from typing import AsyncIterator, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from king.api.rest.schemas import LLMGenerateRequest, LLMGenerateResponse
from king.core.ports.llm import Message
from king.core.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["llm"])


# Dependency для получения LLMService
from king.infrastructure.dependencies import get_llm_service


@router.post("/generate", response_model=LLMGenerateResponse)
async def generate(
    request: LLMGenerateRequest,
    llm_service: Optional[LLMService] = Depends(get_llm_service),
) -> LLMGenerateResponse:
    """
    Генерация ответа от LLM

    Args:
        request: Запрос на генерацию
        llm_service: Сервис для работы с LLM

    Returns:
        Результат генерации
    """
    if not llm_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM сервис недоступен. Проверьте настройки GigaChat.",
        )

    # Валидация промпта
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Промпт не может быть пустым",
        )
    
    # Валидация temperature
    if request.temperature is not None:
        if request.temperature < 0 or request.temperature > 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Temperature должен быть в диапазоне от 0 до 2",
            )
    
    # Валидация max_tokens
    if request.max_tokens is not None:
        if request.max_tokens <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="max_tokens должен быть положительным числом",
            )
    
    try:
        # Преобразование контекста в формат Message
        context = None
        if request.context:
            # Валидация контекста
            valid_roles = ["user", "assistant", "system"]
            for i, msg in enumerate(request.context):
                if not isinstance(msg, dict):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Сообщение в контексте на позиции {i} должно быть словарем",
                    )
                msg_role = msg.get("role", "user")
                if msg_role not in valid_roles:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Неверная роль в контексте на позиции {i}: {msg_role}. Доступные роли: {valid_roles}",
                    )
                if not msg.get("content"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Содержимое сообщения в контексте на позиции {i} не может быть пустым",
                    )
            
            context = [
                Message(role=msg.get("role", "user"), content=msg.get("content", ""))
                for msg in request.context
            ]

        # Генерация ответа
        response = await llm_service.generate(
            prompt=request.prompt,
            context=context,
            stream=request.stream,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Если streaming, возвращаем StreamingResponse
        if request.stream:
            return StreamingResponse(
                _stream_generate(response),
                media_type="text/event-stream",
            )

        return LLMGenerateResponse(
            content=response.content,
            model=response.model,
            tokens_used=response.tokens_used,
            metadata=response.metadata,
        )

    except ValueError as e:
        # Ошибки валидации
        logger.warning(f"Ошибка валидации при генерации ответа: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка валидации: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Ошибка при генерации ответа: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации ответа: {str(e)}",
        )


async def _stream_generate(response_stream: AsyncIterator) -> AsyncIterator[str]:
    """
    Генератор для streaming ответов

    Args:
        response_stream: Поток ответов от LLM

    Yields:
        Строки в формате Server-Sent Events
    """
    try:
        async for chunk in response_stream:
            content = chunk.content
            if content:
                yield f"data: {content}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"Ошибка при streaming: {e}", exc_info=True)
        yield f"data: {{'error': '{str(e)}'}}\n\n"


@router.get("/health")
async def health_check(llm_service: Optional[LLMService] = Depends(get_llm_service)) -> dict:
    """
    Проверка доступности LLM сервиса

    Args:
        llm_service: Сервис для работы с LLM

    Returns:
        Статус сервиса
    """
    if not llm_service:
        return {
            "status": "unavailable",
            "service": "llm",
            "message": "LLM сервис не инициализирован",
        }

    is_healthy = await llm_service.health_check()
    return {
        "status": "ok" if is_healthy else "error",
        "service": "llm",
    }

