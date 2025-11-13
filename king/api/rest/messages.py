"""
REST API endpoints для работы с сообщениями
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from king.api.rest.schemas import ConversationResponse, MessageCreate, MessageResponse
from king.core.services.message_processor import MessageProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])


# Dependency для получения MessageProcessor
from king.infrastructure.dependencies import get_message_processor


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    processor: Optional[MessageProcessor] = Depends(get_message_processor),
) -> MessageResponse:
    """
    Создание и обработка сообщения

    Args:
        message_data: Данные сообщения
        processor: Процессор сообщений

    Returns:
        Созданное сообщение
    """
    if not processor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Процессор сообщений недоступен",
        )

    # Валидация содержимого сообщения
    if not message_data.content or not message_data.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Содержимое сообщения не может быть пустым",
        )
    
    # Валидация роли
    valid_roles = ["user", "assistant", "system"]
    if message_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неверная роль: {message_data.role}. Доступные роли: {valid_roles}",
        )
    
    try:
        message = await processor.process_message(
            content=message_data.content,
            role=message_data.role,
            conversation_id=message_data.conversation_id,
            metadata=message_data.metadata,
        )

        return MessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            timestamp=message.timestamp.isoformat(),
            metadata=message.metadata,
            conversation_id=message.conversation_id,
        )
    except ValueError as e:
        # Ошибки валидации
        logger.warning(f"Ошибка валидации при обработке сообщения: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка валидации: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обработке сообщения: {str(e)}",
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    processor: MessageProcessor = Depends(get_message_processor),
) -> ConversationResponse:
    """
    Получение диалога по ID

    Args:
        conversation_id: ID диалога
        processor: Процессор сообщений

    Returns:
        Информация о диалоге
    """
    conversation = await processor.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Диалог с ID {conversation_id} не найден",
        )

    messages = [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            timestamp=msg.timestamp.isoformat(),
            metadata=msg.metadata,
            conversation_id=msg.conversation_id,
        )
        for msg in conversation.messages
    ]

    return ConversationResponse(
        id=conversation.id,
        messages=messages,
        context=conversation.context,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 100,
    processor: MessageProcessor = Depends(get_message_processor),
) -> List[ConversationResponse]:
    """
    Получение списка диалогов

    Args:
        skip: Количество пропущенных записей
        limit: Максимальное количество записей
        processor: Процессор сообщений

    Returns:
        Список диалогов
    """
    conversations = await processor.get_all_conversations(skip=skip, limit=limit)

    return [
        ConversationResponse(
            id=conv.id,
            messages=[
                MessageResponse(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp.isoformat(),
                    metadata=msg.metadata,
                    conversation_id=msg.conversation_id,
                )
                for msg in conv.messages
            ],
            context=conv.context,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
        )
        for conv in conversations
    ]

