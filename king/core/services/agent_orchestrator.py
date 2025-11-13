"""
AgentOrchestrator - оркестрация агентов
"""

import logging
from typing import List, Optional

from king.core.domain import Agent, AgentCreated, AgentStatus, AgentStatusChanged, Task
from king.core.ports.repositories import IAgentRepository, ITaskRepository

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Оркестратор для управления агентами и распределения задач
    """

    def __init__(
        self,
        agent_repository: IAgentRepository,
        task_repository: ITaskRepository,
        event_bus: Optional[object] = None,
    ):
        """
        Инициализация оркестратора

        Args:
            agent_repository: Репозиторий агентов
            task_repository: Репозиторий задач
            event_bus: Event bus для публикации событий (опционально)
        """
        self.agent_repository = agent_repository
        self.task_repository = task_repository
        self.event_bus = event_bus

    async def create_agent(
        self,
        name: str,
        agent_type: str,
        capabilities: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> Agent:
        """
        Создание нового агента

        Args:
            name: Имя агента
            agent_type: Тип агента
            capabilities: Возможности агента
            metadata: Дополнительные метаданные

        Returns:
            Созданный агент
        """
        from king.core.domain import AgentType

        agent = Agent(
            name=name,
            type=AgentType(agent_type) if isinstance(agent_type, str) else agent_type,
            status=AgentStatus.CREATED,
            capabilities=capabilities or {},
            metadata=metadata or {},
        )

        agent = await self.agent_repository.create(agent)

        # Публикация события создания агента
        if self.event_bus:
            event = AgentCreated(
                agent_id=agent.id,
                agent_name=agent.name,
                agent_type=agent.type.value,
                capabilities=agent.capabilities,
            )
            await self._publish_event(event)

        logger.info(f"Создан агент: {agent.id} ({agent.name})")
        return agent

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Получение агента по ID

        Args:
            agent_id: ID агента

        Returns:
            Агент или None если не найден
        """
        return await self.agent_repository.get_by_id(agent_id)

    async def get_all_agents(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        """
        Получение всех агентов

        Args:
            skip: Количество пропущенных записей
            limit: Максимальное количество записей

        Returns:
            Список агентов
        """
        return await self.agent_repository.get_all(skip=skip, limit=limit)

    async def update_agent_status(
        self, agent_id: str, new_status: AgentStatus, reason: Optional[str] = None
    ) -> Agent:
        """
        Обновление статуса агента

        Args:
            agent_id: ID агента
            new_status: Новый статус
            reason: Причина изменения статуса

        Returns:
            Обновленный агент
        """
        agent = await self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise ValueError(f"Агент с ID {agent_id} не найден")

        old_status = agent.status
        agent.change_status(new_status, reason)
        agent = await self.agent_repository.update(agent)

        # Публикация события изменения статуса
        if self.event_bus:
            event = AgentStatusChanged(
                agent_id=agent.id,
                old_status=old_status.value,
                new_status=new_status.value,
                reason=reason,
            )
            await self._publish_event(event)

        logger.info(f"Статус агента {agent_id} изменен: {old_status.value} -> {new_status.value}")
        return agent

    async def assign_task_to_agent(self, task: Task, agent_id: str) -> Task:
        """
        Назначение задачи агенту

        Args:
            task: Задача для назначения
            agent_id: ID агента

        Returns:
            Обновленная задача
        """
        agent = await self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise ValueError(f"Агент с ID {agent_id} не найден")

        if not agent.is_available():
            raise ValueError(f"Агент {agent_id} недоступен для выполнения задач")

        task.assign_to(agent_id)
        task = await self.task_repository.update(task)

        logger.info(f"Задача {task.id} назначена агенту {agent_id}")
        return task

    async def find_available_agent(self, required_capabilities: Optional[List[str]] = None) -> Optional[Agent]:
        """
        Поиск доступного агента с требуемыми возможностями

        Args:
            required_capabilities: Список требуемых возможностей

        Returns:
            Доступный агент или None
        """
        available_agents = await self.agent_repository.get_available()

        if not available_agents:
            return None

        # Если требуются специфические возможности, фильтруем агентов
        if required_capabilities:
            for agent in available_agents:
                if all(agent.has_capability(cap) for cap in required_capabilities):
                    return agent
            return None

        # Возвращаем первого доступного агента
        return available_agents[0] if available_agents else None

    async def get_agent_tasks(self, agent_id: str) -> List[Task]:
        """
        Получение задач, назначенных агенту

        Args:
            agent_id: ID агента

        Returns:
            Список задач агента
        """
        return await self.task_repository.get_by_agent(agent_id)

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

