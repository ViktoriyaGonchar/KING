"""
REST API endpoint для Prometheus метрик
"""

from fastapi import APIRouter
from fastapi.responses import Response

from king.infrastructure.metrics import get_metrics

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics() -> Response:
    """
    Endpoint для Prometheus метрик

    Returns:
        Метрики в формате Prometheus text format
    """
    metrics_data = get_metrics()
    return Response(content=metrics_data, media_type="text/plain; version=0.0.4")

