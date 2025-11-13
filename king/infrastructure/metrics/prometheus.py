"""
Prometheus метрики для платформы KING
"""

import logging
import time
from functools import wraps
from typing import Callable, Optional

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
    start_http_server,
)

logger = logging.getLogger(__name__)

# Системные метрики
http_requests_total = Counter(
    "king_http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "king_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

# Бизнес-метрики
llm_requests_total = Counter(
    "king_llm_requests_total",
    "Total number of LLM requests",
    ["provider", "model", "status"],
)

llm_request_duration_seconds = Histogram(
    "king_llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["provider", "model"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
)

llm_tokens_total = Counter(
    "king_llm_tokens_total",
    "Total number of LLM tokens",
    ["provider", "model", "type"],  # type: input, output
)

agents_active = Gauge(
    "king_agents_active",
    "Number of active agents",
    ["status"],
)

tasks_total = Counter(
    "king_tasks_total",
    "Total number of tasks",
    ["type", "status"],
)

tasks_duration_seconds = Histogram(
    "king_tasks_duration_seconds",
    "Task execution duration in seconds",
    ["type"],
)

messages_total = Counter(
    "king_messages_total",
    "Total number of messages",
    ["role"],
)

# Информационные метрики
app_info = Info(
    "king_app",
    "Application information",
)

# Метрики событий
domain_events_total = Counter(
    "king_domain_events_total",
    "Total number of domain events",
    ["event_type"],
)


def record_http_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """
    Запись метрик HTTP запроса

    Args:
        method: HTTP метод
        endpoint: Endpoint
        status_code: HTTP статус код
        duration: Длительность запроса в секундах
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_llm_metrics(
    provider: str,
    model: Optional[str],
    status: str,
    duration: float,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
):
    """
    Запись метрик LLM запроса

    Args:
        provider: Провайдер LLM (GigaChat, OpenAI и т.д.)
        model: Модель
        status: Статус запроса (success, error)
        duration: Длительность запроса в секундах
        input_tokens: Количество входных токенов
        output_tokens: Количество выходных токенов
    """
    llm_requests_total.labels(
        provider=provider, model=model or "unknown", status=status
    ).inc()
    llm_request_duration_seconds.labels(provider=provider, model=model or "unknown").observe(
        duration
    )

    if input_tokens:
        llm_tokens_total.labels(provider=provider, model=model or "unknown", type="input").inc(
            input_tokens
        )
    if output_tokens:
        llm_tokens_total.labels(provider=provider, model=model or "unknown", type="output").inc(
            output_tokens
        )


def record_domain_event(event_type: str):
    """
    Запись метрики доменного события

    Args:
        event_type: Тип события
    """
    domain_events_total.labels(event_type=event_type).inc()


def record_task_metrics(task_type: str, status: str, duration: Optional[float] = None):
    """
    Запись метрик задачи

    Args:
        task_type: Тип задачи
        status: Статус задачи
        duration: Длительность выполнения (опционально)
    """
    tasks_total.labels(type=task_type, status=status).inc()
    if duration is not None:
        tasks_duration_seconds.labels(type=task_type).observe(duration)


def record_message_metrics(role: str):
    """
    Запись метрик сообщения

    Args:
        role: Роль сообщения (user, assistant, system)
    """
    messages_total.labels(role=role).inc()


def update_agents_metrics(status: str, count: int):
    """
    Обновление метрик агентов

    Args:
        status: Статус агентов
        count: Количество агентов
    """
    agents_active.labels(status=status).set(count)


def setup_metrics(app_name: str = "KING", app_version: str = "1.0.0", port: int = 9090) -> None:
    """
    Настройка и запуск Prometheus метрик

    Args:
        app_name: Название приложения
        app_version: Версия приложения
        port: Порт для метрик endpoint
    """
    # Установка информационных метрик
    app_info.info({"name": app_name, "version": app_version})

    # Запуск HTTP сервера для метрик
    try:
        start_http_server(port)
        logger.info(f"Prometheus метрики доступны на порту {port}")
    except OSError as e:
        logger.warning(f"Не удалось запустить Prometheus HTTP сервер: {e}")


def get_metrics() -> bytes:
    """
    Получение метрик в формате Prometheus

    Returns:
        Метрики в формате Prometheus text format
    """
    return generate_latest()


def timing_metric(metric: Histogram, labels: Optional[dict] = None):
    """
    Декоратор для измерения времени выполнения функции

    Args:
        metric: Prometheus Histogram метрика
        labels: Метки для метрики

    Returns:
        Декоратор
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
                raise

        # Возвращаем соответствующий wrapper
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator

