"""
MessageProcessor - обработка входящих сообщений
"""

import logging
from typing import List, Optional

from king.core.domain import (
    Conversation,
    Message,
    MessageProcessed,
    MessageReceived,
)
from king.core.ports.repositories import IMessageRepository
from king.core.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class MessageProcessor:
    """
    Процессор сообщений
    Обрабатывает входящие сообщения, маршрутизирует их и генерирует ответы
    """

    def __init__(
        self,
        message_repository: IMessageRepository,
        llm_service: Optional[LLMService] = None,
        event_bus: Optional[object] = None,
    ):
        """
        Инициализация процессора сообщений

        Args:
            message_repository: Репозиторий сообщений
            llm_service: Сервис для работы с LLM (опционально)
            event_bus: Event bus для публикации событий (опционально)
        """
        self.message_repository = message_repository
        self.llm_service = llm_service
        self.event_bus = event_bus

    async def process_message(
        self,
        content: str,
        role: str = "user",
        conversation_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Message:
        """
        Обработка входящего сообщения

        Args:
            content: Содержимое сообщения
            role: Роль отправителя (user, system, assistant)
            conversation_id: ID диалога (если None, создается новый)
            metadata: Дополнительные метаданные

        Returns:
            Обработанное сообщение
        """
        # Создание или получение диалога
        conversation = None
        if conversation_id:
            conversation = await self.message_repository.get_conversation_by_id(conversation_id)

        if not conversation:
            conversation = Conversation(metadata=metadata or {})
            conversation = await self.message_repository.create_conversation(conversation)

        # Создание сообщения
        message = Message(
            role=role,
            content=content,
            conversation_id=conversation.id,
            metadata=metadata or {},
        )

        message = await self.message_repository.create_message(message)
        await self.message_repository.add_message_to_conversation(conversation.id, message)

        # Публикация события получения сообщения
        if self.event_bus:
            event = MessageReceived(
                message_id=message.id,
                role=message.role,
                content=message.content,
                conversation_id=conversation.id,
            )
            await self._publish_event(event)

        logger.info(f"Обработано сообщение: {message.id} в диалоге {conversation.id}")

        # Если это сообщение от пользователя и есть LLM сервис, генерируем ответ
        if role == "user" and self.llm_service:
            await self._generate_response(conversation, message)

        return message

    async def _generate_response(self, conversation: Conversation, user_message: Message) -> None:
        """
        Генерация ответа на сообщение пользователя

        Args:
            conversation: Диалог
            user_message: Сообщение пользователя
        """
        try:
            # Получение истории диалога
            messages = await self.message_repository.get_conversation_messages(conversation.id)

            # Преобразование в формат для LLM
            context = []
            for msg in messages:
                context.append(
                    Message(
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.timestamp,
                    )
                )

            # Генерация ответа через LLM
            prompt = user_message.content
            response = await self.llm_service.generate(prompt, context=context)

            # Создание сообщения-ответа
            assistant_message = Message(
                role="assistant",
                content=response.content,
                conversation_id=conversation.id,
                metadata={"model": response.model, "tokens_used": response.tokens_used},
            )

            assistant_message = await self.message_repository.create_message(assistant_message)
            await self.message_repository.add_message_to_conversation(
                conversation.id, assistant_message
            )

            # Публикация события обработки сообщения
            if self.event_bus:
                event = MessageProcessed(
                    message_id=user_message.id,
                    response=assistant_message.content,
                )
                await self._publish_event(event)

            logger.info(f"Сгенерирован ответ на сообщение {user_message.id}")

        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}", exc_info=True)
            raise

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Получение диалога по ID

        Args:
            conversation_id: ID диалога

        Returns:
            Диалог или None если не найден
        """
        return await self.message_repository.get_conversation_by_id(conversation_id)

    async def get_conversation_messages(
        self, conversation_id: str, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        """
        Получение сообщений диалога

        Args:
            conversation_id: ID диалога
            skip: Количество пропущенных записей
            limit: Максимальное количество записей

        Returns:
            Список сообщений
        """
        return await self.message_repository.get_conversation_messages(
            conversation_id, skip=skip, limit=limit
        )

    async def get_all_conversations(self, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """
        Получение всех диалогов

        Args:
            skip: Количество пропущенных записей
            limit: Максимальное количество записей

        Returns:
            Список диалогов
        """
        return await self.message_repository.get_all_conversations(skip=skip, limit=limit)

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

