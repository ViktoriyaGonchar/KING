"""
Настройки приложения с валидацией через Pydantic
"""

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Настройки базы данных"""

    url: str = Field(..., description="URL подключения к БД")
    pool_size: int = Field(default=10, description="Размер пула соединений")
    max_overflow: int = Field(default=20, description="Максимальное переполнение пула")
    echo: bool = Field(default=False, description="Логирование SQL запросов")

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class RedisSettings(BaseSettings):
    """Настройки Redis"""

    url: str = Field(default="redis://localhost:6379/0", description="URL подключения к Redis")
    decode_responses: bool = Field(default=True, description="Декодирование ответов")

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class KafkaSettings(BaseSettings):
    """Настройки Kafka"""

    bootstrap_servers: str = Field(
        default="localhost:9092", description="Bootstrap серверы Kafka"
    )
    topic_prefix: str = Field(default="king", description="Префикс топиков")
    consumer_group: Optional[str] = Field(default=None, description="Группа потребителей")

    model_config = SettingsConfigDict(env_prefix="KAFKA_")


class GigaChatSettings(BaseSettings):
    """Настройки GigaChat"""

    client_id: str = Field(..., description="Client ID для GigaChat")
    client_secret: str = Field(..., description="Client Secret для GigaChat")
    scope: str = Field(
        default="https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        description="OAuth scope",
    )
    base_url: str = Field(
        default="https://gigachat.devices.sberbank.ru/api/v1",
        description="Базовый URL API GigaChat",
    )

    model_config = SettingsConfigDict(env_prefix="GIGACHAT_")


class AppSettings(BaseSettings):
    """Основные настройки приложения"""

    name: str = Field(default="KING", description="Название приложения")
    version: str = Field(default="1.0.0", description="Версия приложения")
    debug: bool = Field(default=False, description="Режим отладки")
    log_level: str = Field(default="INFO", description="Уровень логирования")
    secret_key: str = Field(..., description="Секретный ключ приложения")
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Разрешенные источники для CORS",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Валидация уровня логирования"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level должен быть одним из: {valid_levels}")
        return v.upper()

    model_config = SettingsConfigDict(env_prefix="APP_")


class ObservabilitySettings(BaseSettings):
    """Настройки observability"""

    jaeger_endpoint: Optional[str] = Field(
        default=None, description="Endpoint Jaeger для трейсинга"
    )
    prometheus_port: int = Field(default=9090, description="Порт для метрик Prometheus")
    enable_tracing: bool = Field(default=True, description="Включить трейсинг")

    model_config = SettingsConfigDict(env_prefix="OBSERVABILITY_")


class Settings(BaseSettings):
    """Корневой класс настроек приложения"""

    app: AppSettings = Field(default_factory=AppSettings)
    database: Optional[DatabaseSettings] = None
    redis: Optional[RedisSettings] = None
    kafka: Optional[KafkaSettings] = None
    gigachat: Optional[GigaChatSettings] = None
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",  # Для вложенных настроек: APP__DEBUG
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def load_from_file(cls, config_path: Path) -> "Settings":
        """
        Загрузка настроек из файла конфигурации

        Args:
            config_path: Путь к файлу конфигурации (YAML/JSON)

        Returns:
            Экземпляр Settings
        """
        # Сначала загружаем из переменных окружения
        settings = cls()

        # Затем перезаписываем значениями из файла (если есть)
        if config_path.exists():
            import yaml

            with open(config_path, "r", encoding="utf-8") as f:
                if config_path.suffix in [".yaml", ".yml"]:
                    file_config = yaml.safe_load(f) or {}
                else:
                    import json

                    file_config = json.load(f) or {}

            # Обновляем настройки значениями из файла
            # Pydantic автоматически обработает вложенные структуры
            settings = cls.model_validate({**settings.model_dump(), **file_config})

        return settings


# Глобальный экземпляр настроек (будет инициализирован при старте приложения)
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Получение глобальных настроек приложения

    Returns:
        Экземпляр Settings

    Raises:
        RuntimeError: Если настройки не инициализированы
    """
    if settings is None:
        raise RuntimeError("Настройки не инициализированы. Вызовите init_settings()")
    return settings


def init_settings(config_path: Optional[Path] = None) -> Settings:
    """
    Инициализация настроек приложения

    Args:
        config_path: Путь к файлу конфигурации (опционально)

    Returns:
        Экземпляр Settings
    """
    global settings

    if config_path:
        settings = Settings.load_from_file(config_path)
    else:
        settings = Settings()

    return settings

