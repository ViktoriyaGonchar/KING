"""
Middleware для автоматического сбора метрик HTTP запросов
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from king.infrastructure.metrics import record_http_metrics

logger = None  # Будет инициализирован при первом использовании


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware для сбора метрик HTTP запросов"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обработка запроса с записью метрик

        Args:
            request: HTTP запрос
            call_next: Следующий обработчик

        Returns:
            HTTP ответ
        """
        start_time = time.time()

        # Получение информации о запросе
        method = request.method
        endpoint = request.url.path

        # Исключаем метрики и health check из детального логирования
        if endpoint in ["/metrics", "/health", "/docs", "/openapi.json", "/redoc"]:
            endpoint = endpoint
        else:
            # Нормализация endpoint (убираем ID из пути)
            endpoint = self._normalize_endpoint(endpoint)

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            record_http_metrics(method=method, endpoint=endpoint, status_code=status_code, duration=duration)

        return response

    def _normalize_endpoint(self, path: str) -> str:
        """
        Нормализация endpoint для метрик
        Заменяет ID на {id} для группировки

        Args:
            path: Путь запроса

        Returns:
            Нормализованный путь
        """
        # Простая нормализация - заменяем UUID-подобные строки
        import re

        # Заменяем UUID на {id}
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        normalized = re.sub(uuid_pattern, "{id}", path, flags=re.IGNORECASE)

        # Заменяем длинные числовые ID на {id}
        normalized = re.sub(r"/\d{10,}/", "/{id}/", normalized)

        return normalized

