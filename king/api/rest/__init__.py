"""
REST API endpoints
"""

from fastapi import APIRouter

from king.api.rest import agents, health, llm, messages, metrics, tasks

# Создание главного роутера
router = APIRouter(prefix="/api/v1")

# Подключение роутеров
router.include_router(agents.router)
router.include_router(tasks.router)
router.include_router(messages.router)
router.include_router(llm.router)

# Метрики и health check на корневом уровне (не в /api/v1)
root_router = APIRouter()
root_router.include_router(metrics.router)
root_router.include_router(health.router)

__all__ = ["router", "root_router"]
