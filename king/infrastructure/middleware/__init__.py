"""
Middleware для FastAPI
"""

from king.infrastructure.middleware.metrics_middleware import MetricsMiddleware

__all__ = ["MetricsMiddleware"]

