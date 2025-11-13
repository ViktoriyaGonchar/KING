# Система конфигурации KING Platform

## Обзор

Система конфигурации поддерживает несколько способов загрузки настроек:
1. **EnvironmentConfig** - из переменных окружения и .env файлов
2. **ConfigLoader** - из YAML/JSON файлов
3. **Settings** - валидированные настройки через Pydantic

## Использование

### 1. EnvironmentConfig

```python
from king.infrastructure.config import EnvironmentConfig

# Загрузка из .env файла
config = EnvironmentConfig(env_file=Path(".env"))

# Получение значений
db_host = config.get("database.host", "localhost")
db_port = config.get_int("database.port", 5432)
debug = config.get_bool("app.debug", False)
secret = config.get_secret("gigachat.client_secret")
```

### 2. ConfigLoader

```python
from king.infrastructure.config import ConfigLoader
from pathlib import Path

# Загрузка из YAML файла
config = ConfigLoader(Path("config/app.yaml"))

# Получение значений
db_url = config.get("database.url")
app_name = config.get("app.name", "KING")
```

### 3. Settings (Рекомендуется)

```python
from king.infrastructure.config import init_settings, get_settings
from pathlib import Path

# Инициализация при старте приложения
settings = init_settings(config_path=Path("config/app.yaml"))

# Использование в коде
settings = get_settings()
print(settings.app.name)
print(settings.database.url)
print(settings.gigachat.client_id)
```

## Переменные окружения

Переменные окружения поддерживают вложенные ключи через двойное подчеркивание:

```bash
# Для app.debug
APP__DEBUG=true

# Для database.url
DATABASE__URL=postgresql://localhost:5432/king_db

# Для gigachat.client_id
GIGACHAT__CLIENT_ID=your_id
```

## Приоритет загрузки

1. Переменные окружения (наивысший приоритет)
2. Файл конфигурации (YAML/JSON)
3. Значения по умолчанию

## Пример конфигурационного файла

См. `config/app.yaml` для примера структуры конфигурации.

