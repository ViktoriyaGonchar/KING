"""
Расширенный health check endpoint
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends

from king.infrastructure.dependencies import (
    get_agent_orchestrator,
    get_llm_service,
    get_message_processor,
    get_message_queue,
    get_task_scheduler,
    get_settings_dep,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Readiness check для Kubernetes
    Проверяет готовность всех зависимостей

    Returns:
        Статус готовности
    """
    checks = {
        "dependencies": "ok",
        "repositories": "ok",
    }

    # Проверка сервисов
    try:
        settings = get_settings_dep()
        orchestrator = get_agent_orchestrator()
        scheduler = get_task_scheduler()
        processor = get_message_processor()
        llm_service = get_llm_service()
        message_queue = get_message_queue()

        if orchestrator and scheduler and processor:
            checks["services"] = "ok"
        else:
            checks["services"] = "degraded"
            checks["message"] = "Некоторые сервисы недоступны"

        # Проверка LLM (опционально)
        if llm_service:
            try:
                llm_healthy = await llm_service.health_check()
                checks["llm"] = "ok" if llm_healthy else "degraded"
            except Exception as e:
                logger.warning(f"Ошибка при проверке LLM: {e}")
                checks["llm"] = "error"
        else:
            checks["llm"] = "not_configured"

        # Проверка messaging адаптера (опционально)
        if message_queue:
            try:
                if hasattr(message_queue, "health_check"):
                    mq_healthy = await message_queue.health_check()
                    checks["messaging"] = "ok" if mq_healthy else "degraded"
                else:
                    checks["messaging"] = "ok"  # Если нет метода health_check, считаем OK
            except Exception as e:
                logger.warning(f"Ошибка при проверке messaging: {e}")
                checks["messaging"] = "error"
        else:
            checks["messaging"] = "not_configured"

        # Проверка базы данных (если настроена)
        if settings.database:
            try:
                # Простая проверка - можно расширить с реальным подключением
                checks["database"] = "configured"
                # TODO: Добавить реальную проверку подключения к БД
            except Exception as e:
                logger.warning(f"Ошибка при проверке БД: {e}")
                checks["database"] = "error"
        else:
            checks["database"] = "not_configured"

        # Проверка Redis (если настроен)
        if settings.redis:
            try:
                # Простая проверка - можно расширить с реальным подключением
                checks["redis"] = "configured"
                # TODO: Добавить реальную проверку подключения к Redis
            except Exception as e:
                logger.warning(f"Ошибка при проверке Redis: {e}")
                checks["redis"] = "error"
        else:
            checks["redis"] = "not_configured"

    except Exception as e:
        logger.error(f"Ошибка при проверке готовности: {e}", exc_info=True)
        checks["status"] = "error"
        checks["error"] = str(e)
        return checks

    # Определение общего статуса
    if all(v == "ok" or v == "not_configured" for v in checks.values()):
        checks["status"] = "ready"
    else:
        checks["status"] = "not_ready"

    return checks


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check для Kubernetes
    Проверяет, что приложение работает

    Returns:
        Статус жизнеспособности
    """
    return {
        "status": "alive",
        "service": "KING",
    }

