"""
Интерфейсы репозиториев для доменных сущностей
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from king.core.domain import Agent, Conversation, Message, Task


class IAgentRepository(ABC):
    """Интерфейс репозитория для агентов"""

    @abstractmethod
    async def create(self, agent: Agent) -> Agent:
        """
        Создание нового агента

        Args:
            agent: Агент для создания

        Returns:
            Созданный агент
        """
        pass

    @abstractmethod
    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """
        Получение агента по ID

        Args:
            agent_id: ID агента

        Returns:
            Агент или None если не найден
        """
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        """
        Получение всех агентов

        Args:
            skip: Количество пропущенных записей
            limit: Максимальное количество записей

        Returns:
            Список агентов
        """
        pass

    @abstractmethod
    async def update(self, agent: Agent) -> Agent:
        """
        Обновление агента

        Args:
            agent: Агент для обновления

        Returns:
            Обновленный агент
        """
        pass

    @abstractmethod
    async def delete(self, agent_id: str) -> bool:
        """
        Удаление агента

        Args:
            agent_id: ID агента

        Returns:
            True если удален, False если не найден
        """
        pass

    @abstractmethod
    async def get_by_status(self, status: str) -> List[Agent]:
        """
        Получение агентов по статусу

        Args:
            status: Статус агентов

        Returns:
            Список агентов с указанным статусом
        """
        pass

    @abstractmethod
    async def get_available(self) -> List[Agent]:
        """
        Получение доступных агентов (для выполнения задач)

        Returns:
            Список доступных агентов
        """
        pass


class ITaskRepository(ABC):
    """Интерфейс репозитория для задач"""

    @abstractmethod
    async def create(self, task: Task) -> Task:
        """
        Создание новой задачи

        Args:
            task: Задача для создания

        Returns:
            Созданная задача
        """
        pass

    @abstractmethod
    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """
        Получение задачи по ID

        Args:
            task_id: ID задачи

        Returns:
            Задача или None если не найдена
        """
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Task]:
        """
        Получение всех задач

        Args:
            skip: Количество пропущенных записей
            limit: Максимальное количество записей

        Returns:
            Список задач
        """
        pass

    @abstractmethod
    async def update(self, task: Task) -> Task:
        """
        Обновление задачи

        Args:
            task: Задача для обновления

        Returns:
            Обновленная задача
        """
        pass

    @abstractmethod
    async def delete(self, task_id: str) -> bool:
        """
        Удаление задачи

        Args:
            task_id: ID задачи

        Returns:
            True если удалена, False если не найдена
        """
        pass

    @abstractmethod
    async def get_by_status(self, status: str) -> List[Task]:
        """
        Получение задач по статусу

        Args:
            status: Статус задач

        Returns:
            Список задач с указанным статусом
        """
        pass

    @abstractmethod
    async def get_by_agent(self, agent_id: str) -> List[Task]:
        """
        Получение задач, назначенных агенту

        Args:
            agent_id: ID агента

        Returns:
            Список задач агента
        """
        pass

    @abstractmethod
    async def get_pending(self) -> List[Task]:
        """
        Получение задач, ожидающих выполнения

        Returns:
            Список задач в статусе CREATED или ASSIGNED
        """
        pass


class IMessageRepository(ABC):
    """Интерфейс репозитория для сообщений и диалогов"""

    @abstractmethod
    async def create_message(self, message: Message) -> Message:
        """
        Создание нового сообщения

        Args:
            message: Сообщение для создания

        Returns:
            Созданное сообщение
        """
        pass

    @abstractmethod
    async def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """
        Получение сообщения по ID

        Args:
            message_id: ID сообщения

        Returns:
            Сообщение или None если не найдено
        """
        pass

    @abstractmethod
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """
        Создание нового диалога

        Args:
            conversation: Диалог для создания

        Returns:
            Созданный диалог
        """
        pass

    @abstractmethod
    async def get_conversation_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Получение диалога по ID

        Args:
            conversation_id: ID диалога

        Returns:
            Диалог или None если не найден
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def add_message_to_conversation(
        self, conversation_id: str, message: Message
    ) -> Message:
        """
        Добавление сообщения в диалог

        Args:
            conversation_id: ID диалога
            message: Сообщение для добавления

        Returns:
            Добавленное сообщение
        """
        pass

    @abstractmethod
    async def get_all_conversations(self, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """
        Получение всех диалогов

        Args:
            skip: Количество пропущенных записей
            limit: Максимальное количество записей

        Returns:
            Список диалогов
        """
        pass

