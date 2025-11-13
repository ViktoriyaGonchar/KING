"""
In-memory реализации репозиториев для разработки и тестирования
"""

import logging
from typing import Dict, List, Optional

from king.core.domain import Agent, Conversation, Message, Task
from king.core.ports.repositories import (
    IAgentRepository,
    IMessageRepository,
    ITaskRepository,
)

logger = logging.getLogger(__name__)


class InMemoryAgentRepository(IAgentRepository):
    """In-memory реализация репозитория агентов"""

    def __init__(self):
        """Инициализация репозитория"""
        self._agents: Dict[str, Agent] = {}

    async def create(self, agent: Agent) -> Agent:
        """Создание агента"""
        self._agents[agent.id] = agent
        logger.debug(f"Создан агент: {agent.id}")
        return agent

    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """Получение агента по ID"""
        return self._agents.get(agent_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Получение всех агентов"""
        agents = list(self._agents.values())
        return agents[skip : skip + limit]

    async def update(self, agent: Agent) -> Agent:
        """Обновление агента"""
        if agent.id not in self._agents:
            raise ValueError(f"Агент {agent.id} не найден")
        self._agents[agent.id] = agent
        logger.debug(f"Обновлен агент: {agent.id}")
        return agent

    async def delete(self, agent_id: str) -> bool:
        """Удаление агента"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.debug(f"Удален агент: {agent_id}")
            return True
        return False

    async def get_by_status(self, status: str) -> List[Agent]:
        """Получение агентов по статусу"""
        return [agent for agent in self._agents.values() if agent.status.value == status]

    async def get_available(self) -> List[Agent]:
        """Получение доступных агентов"""
        from king.core.domain import AgentStatus

        return [
            agent
            for agent in self._agents.values()
            if agent.status in [AgentStatus.ACTIVE, AgentStatus.IDLE]
        ]


class InMemoryTaskRepository(ITaskRepository):
    """In-memory реализация репозитория задач"""

    def __init__(self):
        """Инициализация репозитория"""
        self._tasks: Dict[str, Task] = {}

    async def create(self, task: Task) -> Task:
        """Создание задачи"""
        self._tasks[task.id] = task
        logger.debug(f"Создана задача: {task.id}")
        return task

    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """Получение задачи по ID"""
        return self._tasks.get(task_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Task]:
        """Получение всех задач"""
        tasks = list(self._tasks.values())
        return tasks[skip : skip + limit]

    async def update(self, task: Task) -> Task:
        """Обновление задачи"""
        if task.id not in self._tasks:
            raise ValueError(f"Задача {task.id} не найдена")
        self._tasks[task.id] = task
        logger.debug(f"Обновлена задача: {task.id}")
        return task

    async def delete(self, task_id: str) -> bool:
        """Удаление задачи"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            logger.debug(f"Удалена задача: {task_id}")
            return True
        return False

    async def get_by_status(self, status: str) -> List[Task]:
        """Получение задач по статусу"""
        return [task for task in self._tasks.values() if task.status.value == status]

    async def get_by_agent(self, agent_id: str) -> List[Task]:
        """Получение задач агента"""
        return [
            task for task in self._tasks.values() if task.assigned_agent == agent_id
        ]

    async def get_pending(self) -> List[Task]:
        """Получение ожидающих задач"""
        from king.core.domain import TaskStatus

        return [
            task
            for task in self._tasks.values()
            if task.status in [TaskStatus.CREATED, TaskStatus.ASSIGNED]
        ]


class InMemoryMessageRepository(IMessageRepository):
    """In-memory реализация репозитория сообщений"""

    def __init__(self):
        """Инициализация репозитория"""
        self._messages: Dict[str, Message] = {}
        self._conversations: Dict[str, Conversation] = {}

    async def create_message(self, message: Message) -> Message:
        """Создание сообщения"""
        self._messages[message.id] = message
        logger.debug(f"Создано сообщение: {message.id}")
        return message

    async def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Получение сообщения по ID"""
        return self._messages.get(message_id)

    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Создание диалога"""
        self._conversations[conversation.id] = conversation
        logger.debug(f"Создан диалог: {conversation.id}")
        return conversation

    async def get_conversation_by_id(
        self, conversation_id: str
    ) -> Optional[Conversation]:
        """Получение диалога по ID"""
        return self._conversations.get(conversation_id)

    async def get_conversation_messages(
        self, conversation_id: str, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        """Получение сообщений диалога"""
        messages = [
            msg
            for msg in self._messages.values()
            if msg.conversation_id == conversation_id
        ]
        # Сортировка по timestamp
        messages.sort(key=lambda m: m.timestamp)
        return messages[skip : skip + limit]

    async def add_message_to_conversation(
        self, conversation_id: str, message: Message
    ) -> Message:
        """Добавление сообщения в диалог"""
        conversation = await self.get_conversation_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Диалог {conversation_id} не найден")

        conversation.add_message(message)
        await self.create_message(message)
        return message

    async def get_all_conversations(
        self, skip: int = 0, limit: int = 100
    ) -> List[Conversation]:
        """Получение всех диалогов"""
        conversations = list(self._conversations.values())
        return conversations[skip : skip + limit]

