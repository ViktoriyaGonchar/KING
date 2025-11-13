"""
Логирование (OpenTelemetry)
"""

from king.infrastructure.logging.setup import get_logger, setup_logging

__all__ = [
    "setup_logging",
    "get_logger",
]
