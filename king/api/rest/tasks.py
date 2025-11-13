"""
REST API endpoints для управления задачами
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from king.api.rest.schemas import TaskCreate, TaskResponse
from king.core.services.task_scheduler import TaskScheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


# Dependency для получения TaskScheduler
from king.infrastructure.dependencies import get_task_scheduler


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    scheduler: TaskScheduler = Depends(get_task_scheduler),
) -> TaskResponse:
    """
    Создание новой задачи

    Args:
        task_data: Данные для создания задачи
        scheduler: Планировщик задач

    Returns:
        Созданная задача
    """
    # Валидация типа задачи
    from king.core.domain.task import TaskType
    try:
        task_type_enum = TaskType(task_data.type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неверный тип задачи: {task_data.type}. Доступные типы: {[t.value for t in TaskType]}",
        )
    
    # Валидация payload
    if not task_data.payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload задачи не может быть пустым",
        )
    
    # Валидация приоритета
    if task_data.priority < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Приоритет задачи не может быть отрицательным",
        )
    
    try:
        task = await scheduler.create_task(
            task_type=task_type_enum,
            payload=task_data.payload,
            priority=task_data.priority,
            metadata=task_data.metadata,
        )

        return TaskResponse(
            id=task.id,
            type=task.type.value,
            status=task.status.value,
            payload=task.payload,
            assigned_agent=task.assigned_agent,
            result=task.result,
            error=task.error,
            metadata=task.metadata,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
        )
    except ValueError as e:
        # Ошибки валидации
        logger.warning(f"Ошибка валидации при создании задачи: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка валидации: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Ошибка при создании задачи: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании задачи: {str(e)}",
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    scheduler: TaskScheduler = Depends(get_task_scheduler),
) -> TaskResponse:
    """
    Получение задачи по ID

    Args:
        task_id: ID задачи
        scheduler: Планировщик задач

    Returns:
        Информация о задаче
    """
    task = await scheduler.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с ID {task_id} не найдена",
        )

    return TaskResponse(
        id=task.id,
        type=task.type.value,
        status=task.status.value,
        payload=task.payload,
        assigned_agent=task.assigned_agent,
        result=task.result,
        error=task.error,
        metadata=task.metadata,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
    )


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    scheduler: TaskScheduler = Depends(get_task_scheduler),
) -> List[TaskResponse]:
    """
    Получение списка задач

    Args:
        skip: Количество пропущенных записей
        limit: Максимальное количество записей
        status: Фильтр по статусу (опционально)
        scheduler: Планировщик задач

    Returns:
        Список задач
    """
    if status:
        tasks = await scheduler.get_tasks_by_status(status)
    else:
        # Получаем все задачи через репозиторий
        from king.infrastructure.dependencies import get_task_repository
        task_repo = get_task_repository()
        tasks = await task_repo.get_all(skip=skip, limit=limit)

    return [
        TaskResponse(
            id=task.id,
            type=task.type.value,
            status=task.status.value,
            payload=task.payload,
            assigned_agent=task.assigned_agent,
            result=task.result,
            error=task.error,
            metadata=task.metadata,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
        )
        for task in tasks
    ]


@router.post("/{task_id}/schedule", response_model=TaskResponse)
async def schedule_task(
    task_id: str,
    scheduler: TaskScheduler = Depends(get_task_scheduler),
) -> TaskResponse:
    """
    Планирование задачи (назначение агенту)

    Args:
        task_id: ID задачи
        scheduler: Планировщик задач

    Returns:
        Обновленная задача
    """
    try:
        task = await scheduler.schedule_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Задача {task_id} не найдена",
            )

        return TaskResponse(
            id=task.id,
            type=task.type.value,
            status=task.status.value,
            payload=task.payload,
            assigned_agent=task.assigned_agent,
            result=task.result,
            error=task.error,
            metadata=task.metadata,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
        )
    except Exception as e:
        logger.error(f"Ошибка при планировании задачи: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при планировании задачи: {str(e)}",
        )

