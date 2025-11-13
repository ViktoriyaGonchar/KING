"""
TaskScheduler - планирование и распределение задач
"""

import logging
from typing import List, Optional

from king.core.domain import Task, TaskAssigned, TaskCreated, TaskStatus, TaskType
from king.core.ports.repositories import IAgentRepository, ITaskRepository

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Планировщик задач
    Обеспечивает планирование, приоритизацию и распределение задач по агентам
    """

    def __init__(
        self,
        task_repository: ITaskRepository,
        agent_repository: IAgentRepository,
        agent_orchestrator: Optional[object] = None,
        event_bus: Optional[object] = None,
    ):
        """
        Инициализация планировщика задач

        Args:
            task_repository: Репозиторий задач
            agent_repository: Репозиторий агентов
            agent_orchestrator: Оркестратор агентов (опционально)
            event_bus: Event bus для публикации событий (опционально)
        """
        self.task_repository = task_repository
        self.agent_repository = agent_repository
        self.agent_orchestrator = agent_orchestrator
        self.event_bus = event_bus

    async def create_task(
        self,
        task_type: str,
        payload: dict,
        priority: int = 0,
        metadata: Optional[dict] = None,
    ) -> Task:
        """
        Создание новой задачи

        Args:
            task_type: Тип задачи
            payload: Данные задачи
            priority: Приоритет задачи (чем больше, тем выше)
            metadata: Дополнительные метаданные

        Returns:
            Созданная задача
        """
        task = Task(
            type=TaskType(task_type) if isinstance(task_type, str) else task_type,
            status=TaskStatus.CREATED,
            payload=payload,
            metadata={**(metadata or {}), "priority": priority},
        )

        task = await self.task_repository.create(task)

        # Публикация события создания задачи
        if self.event_bus:
            event = TaskCreated(
                task_id=task.id,
                task_type=task.type.value,
                payload=task.payload,
            )
            await self._publish_event(event)

        logger.info(f"Создана задача: {task.id} (тип: {task.type.value})")

        # Автоматическое назначение задачи, если есть оркестратор
        if self.agent_orchestrator:
            await self.schedule_task(task.id)

        return task

    async def schedule_task(self, task_id: str) -> Optional[Task]:
        """
        Планирование задачи (назначение агенту)

        Args:
            task_id: ID задачи

        Returns:
            Обновленная задача или None если не найдена
        """
        task = await self.task_repository.get_by_id(task_id)
        if not task:
            logger.warning(f"Задача {task_id} не найдена")
            return None

        if task.status != TaskStatus.CREATED:
            logger.warning(f"Задача {task_id} уже назначена или выполнена")
            return task

        # Поиск подходящего агента
        required_capabilities = task.metadata.get("required_capabilities")
        agent = None

        if self.agent_orchestrator:
            agent = await self.agent_orchestrator.find_available_agent(required_capabilities)

        if not agent:
            logger.warning(f"Не найден доступный агент для задачи {task_id}")
            return task

        # Назначение задачи агенту
        try:
            if self.agent_orchestrator:
                task = await self.agent_orchestrator.assign_task_to_agent(task, agent.id)
            else:
                task.assign_to(agent.id)
                task = await self.task_repository.update(task)

            # Публикация события назначения задачи
            if self.event_bus:
                event = TaskAssigned(task_id=task.id, agent_id=agent.id)
                await self._publish_event(event)

            logger.info(f"Задача {task_id} назначена агенту {agent.id}")
            return task

        except Exception as e:
            logger.error(f"Ошибка при назначении задачи {task_id}: {e}", exc_info=True)
            return task

    async def get_pending_tasks(self) -> List[Task]:
        """
        Получение задач, ожидающих выполнения

        Returns:
            Список задач в статусе CREATED или ASSIGNED
        """
        return await self.task_repository.get_pending()

    async def schedule_all_pending(self) -> int:
        """
        Планирование всех ожидающих задач

        Returns:
            Количество запланированных задач
        """
        pending_tasks = await self.get_pending_tasks()
        scheduled_count = 0

        for task in pending_tasks:
            scheduled = await self.schedule_task(task.id)
            if scheduled and scheduled.status == TaskStatus.ASSIGNED:
                scheduled_count += 1

        logger.info(f"Запланировано задач: {scheduled_count} из {len(pending_tasks)}")
        return scheduled_count

    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Получение задачи по ID

        Args:
            task_id: ID задачи

        Returns:
            Задача или None если не найдена
        """
        return await self.task_repository.get_by_id(task_id)

    async def get_tasks_by_status(self, status: str) -> List[Task]:
        """
        Получение задач по статусу

        Args:
            status: Статус задач

        Returns:
            Список задач с указанным статусом
        """
        return await self.task_repository.get_by_status(status)

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

