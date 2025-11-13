"""
REST API endpoints для управления агентами
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from king.api.rest.schemas import AgentCreate, AgentResponse
from king.core.domain import AgentStatus, AgentType
from king.core.services.agent_orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


# Dependency для получения AgentOrchestrator
from king.infrastructure.dependencies import get_agent_orchestrator


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
) -> AgentResponse:
    """
    Создание нового агента

    Args:
        agent_data: Данные для создания агента
        orchestrator: Оркестратор агентов

    Returns:
        Созданный агент
    """
    # Валидация типа агента
    try:
        agent_type_enum = AgentType(agent_data.type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неверный тип агента: {agent_data.type}. Доступные типы: {[t.value for t in AgentType]}",
        )
    
    # Валидация имени
    if not agent_data.name or not agent_data.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Имя агента не может быть пустым",
        )
    
    try:
        agent = await orchestrator.create_agent(
            name=agent_data.name,
            agent_type=agent_type_enum,
            capabilities=agent_data.capabilities,
            metadata=agent_data.metadata,
        )

        return AgentResponse(
            id=agent.id,
            name=agent.name,
            type=agent.type.value,
            status=agent.status.value,
            capabilities=agent.capabilities,
            metadata=agent.metadata,
            created_at=agent.created_at.isoformat(),
            updated_at=agent.updated_at.isoformat(),
        )
    except ValueError as e:
        # Ошибки валидации
        logger.warning(f"Ошибка валидации при создании агента: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка валидации: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Ошибка при создании агента: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании агента: {str(e)}",
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
) -> AgentResponse:
    """
    Получение агента по ID

    Args:
        agent_id: ID агента
        orchestrator: Оркестратор агентов

    Returns:
        Информация об агенте
    """
    agent = await orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Агент с ID {agent_id} не найден",
        )

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        type=agent.type.value,
        status=agent.status.value,
        capabilities=agent.capabilities,
        metadata=agent.metadata,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat(),
    )


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    skip: int = 0,
    limit: int = 100,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
) -> List[AgentResponse]:
    """
    Получение списка агентов

    Args:
        skip: Количество пропущенных записей
        limit: Максимальное количество записей
        orchestrator: Оркестратор агентов

    Returns:
        Список агентов
    """
    agents = await orchestrator.get_all_agents(skip=skip, limit=limit)

    return [
        AgentResponse(
            id=agent.id,
            name=agent.name,
            type=agent.type.value,
            status=agent.status.value,
            capabilities=agent.capabilities,
            metadata=agent.metadata,
            created_at=agent.created_at.isoformat(),
            updated_at=agent.updated_at.isoformat(),
        )
        for agent in agents
    ]


@router.patch("/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(
    agent_id: str,
    new_status: str,
    reason: str = None,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
) -> AgentResponse:
    """
    Обновление статуса агента

    Args:
        agent_id: ID агента
        new_status: Новый статус
        reason: Причина изменения статуса
        orchestrator: Оркестратор агентов

    Returns:
        Обновленный агент
    """
    try:
        status_enum = AgentStatus(new_status)
        agent = await orchestrator.update_agent_status(agent_id, status_enum, reason)

        return AgentResponse(
            id=agent.id,
            name=agent.name,
            type=agent.type.value,
            status=agent.status.value,
            capabilities=agent.capabilities,
            metadata=agent.metadata,
            created_at=agent.created_at.isoformat(),
            updated_at=agent.updated_at.isoformat(),
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неверный статус: {new_status}",
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса агента: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении статуса: {str(e)}",
        )

