# GigaChat Adapter

Адаптер для работы с Sber GigaChat API.

## Возможности

- ✅ OAuth2 аутентификация с автоматическим обновлением токенов
- ✅ Поддержка streaming-ответов
- ✅ Retry логика с exponential backoff
- ✅ Обработка rate limits
- ✅ Управление промптами через Jinja2 шаблоны
- ✅ Поддержка истории диалога

## Использование

### Базовое использование

```python
from king.adapters.llm.gigachat import GigaChatAdapter
from king.core.services.llm_service import LLMService

# Создание адаптера
adapter = GigaChatAdapter(
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Использование через сервис
llm_service = LLMService(adapter)

# Генерация ответа
response = await llm_service.generate("Привет, как дела?")
print(response.content)
```

### С историей диалога

```python
from king.core.ports.llm import Message

# История диалога
context = [
    Message(role="user", content="Привет"),
    Message(role="assistant", content="Здравствуйте! Чем могу помочь?"),
]

# Генерация с контекстом
response = await llm_service.generate(
    "Расскажи о погоде",
    context=context
)
```

### Streaming

```python
# Streaming-генерация
async for chunk in llm_service.generate("Расскажи историю", stream=True):
    print(chunk.content, end="", flush=True)
```

### Настройка параметров

```python
response = await llm_service.generate(
    "Напиши рассказ",
    temperature=0.9,
    max_tokens=2000,
    model="GigaChat-Pro"
)
```

## Конфигурация

Настройки можно задать через переменные окружения:

```bash
GIGACHAT_CLIENT_ID=your_client_id
GIGACHAT_CLIENT_SECRET=your_client_secret
GIGACHAT_SCOPE=https://ngw.devices.sberbank.ru:9443/api/v2/oauth
GIGACHAT_BASE_URL=https://gigachat.devices.sberbank.ru/api/v1
```

Или через Settings:

```python
from king.infrastructure.config import Settings, init_settings

settings = init_settings()
adapter = GigaChatAdapter(
    client_id=settings.gigachat.client_id,
    client_secret=settings.gigachat.client_secret,
    base_url=settings.gigachat.base_url
)
```

## Промпты

Шаблоны промптов находятся в `config/prompts/gigachat/default.yaml`.

Пример шаблона:

```yaml
system: |
  Ты — полезный ассистент платформы KING.
  Отвечай кратко, точно и по делу.

user: |
  {{ user_message }}

context: |
  {% if context %}
  Предыдущие сообщения:
  {% for msg in context %}
  - {{ msg.role }}: {{ msg.content }}
  {% endfor %}
  {% endif %}
```

## Обработка ошибок

Адаптер автоматически обрабатывает:
- Истечение токенов (автоматическое обновление)
- Rate limits (ожидание с Retry-After)
- Серверные ошибки (retry с exponential backoff)
- Сетевые ошибки (retry с задержкой)

## Закрытие ресурсов

Не забудьте закрыть адаптер при завершении:

```python
await adapter.close()
```

Или используйте контекстный менеджер (если реализован).

