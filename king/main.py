"""
Точка входа в приложение KING
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from king.api.rest import root_router, router as rest_router
from king.infrastructure.dependencies import cleanup_dependencies, init_dependencies
from king.infrastructure.logging import setup_logging
from king.infrastructure.metrics import setup_metrics
from king.infrastructure.middleware import MetricsMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    Инициализация и очистка ресурсов
    """
    # Startup
    logger.info("Starting KING platform...")
    
    # Настройка логирования
    try:
        from king.infrastructure.config import get_settings
        
        settings = get_settings()
        setup_logging(
            log_level=settings.app.log_level,
            json_format=not settings.app.debug,
        )
        logger.info("Логирование настроено")
    except Exception:
        # Если настройки не загружены, используем базовое логирование
        setup_logging()
    
    # Настройка метрик
    try:
        from king.infrastructure.config import get_settings
        
        settings = get_settings()
        setup_metrics(
            app_name=settings.app.name,
            app_version=settings.app.version,
            port=settings.observability.prometheus_port,
        )
        logger.info("Метрики настроены")
    except Exception as e:
        logger.warning(f"Не удалось настроить метрики: {e}")
    
    # Инициализация зависимостей
    try:
        init_dependencies()
        logger.info("Все зависимости инициализированы")
    except Exception as e:
        logger.error(f"Ошибка при инициализации зависимостей: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down KING platform...")
    
    # Очистка ресурсов
    try:
        await cleanup_dependencies()
        logger.info("Ресурсы очищены")
    except Exception as e:
        logger.error(f"Ошибка при очистке ресурсов: {e}", exc_info=True)


def create_app() -> FastAPI:
    """
    Создание и настройка FastAPI приложения
    """
    app = FastAPI(
        title="KING Platform",
        description="Масштабируемая платформа для управления мультимодальными ИИ-агентами",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Middleware
    app.add_middleware(MetricsMiddleware)  # Метрики должны быть первыми
    
    # Настройка CORS из конфигурации
    try:
        from king.infrastructure.config import get_settings
        settings = get_settings()
        allowed_origins = settings.app.allowed_origins
    except Exception:
        # Fallback на безопасные значения по умолчанию
        logger.warning("Не удалось загрузить настройки CORS, используются значения по умолчанию")
        allowed_origins = ["http://localhost:3000", "http://localhost:8000"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Подключение REST API роутеров
    app.include_router(rest_router)
    app.include_router(root_router)  # Метрики и health check на корневом уровне
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint (legacy, используйте /ready или /live)"""
        return {
            "status": "ok",
            "service": "KING",
            "version": "1.0.0"
        }
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "KING Platform API",
            "version": "1.0.0",
            "docs": "/docs"
        }
    
    return app


def main():
    """Запуск приложения"""
    import uvicorn
    
    app = create_app()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()

