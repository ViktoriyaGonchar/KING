# REST API Documentation

KING Platform REST API предоставляет endpoints для управления агентами, задачами, сообщениями и работы с LLM.

## Базовый URL

```
http://localhost:8000/api/v1
```

## Документация

После запуска приложения доступна интерактивная документация:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

### Агенты (`/agents`)

#### Создание агента
```http
POST /api/v1/agents
Content-Type: application/json

{
  "name": "My Agent",
  "type": "llm",
  "capabilities": {"text_generation": true},
  "metadata": {}
}
```

#### Получение агента
```http
GET /api/v1/agents/{agent_id}
```

#### Список агентов
```http
GET /api/v1/agents?skip=0&limit=100
```

#### Обновление статуса агента
```http
PATCH /api/v1/agents/{agent_id}/status?new_status=active&reason=Started
```

### Задачи (`/tasks`)

#### Создание задачи
```http
POST /api/v1/tasks
Content-Type: application/json

{
  "type": "llm_generation",
  "payload": {"prompt": "Привет"},
  "priority": 1,
  "metadata": {}
}
```

#### Список задач
```http
GET /api/v1/tasks?skip=0&limit=100&status=created
```

#### Планирование задачи
```http
POST /api/v1/tasks/{task_id}/schedule
```

### Сообщения (`/messages`)

#### Отправка сообщения
```http
POST /api/v1/messages
Content-Type: application/json

{
  "content": "Привет, как дела?",
  "role": "user",
  "conversation_id": null,
  "metadata": {}
}
```

#### Получение диалога
```http
GET /api/v1/messages/conversations/{conversation_id}
```

#### Список диалогов
```http
GET /api/v1/messages/conversations?skip=0&limit=100
```

### LLM (`/llm`)

#### Генерация ответа
```http
POST /api/v1/llm/generate
Content-Type: application/json

{
  "prompt": "Расскажи о погоде",
  "context": [
    {"role": "user", "content": "Привет"},
    {"role": "assistant", "content": "Здравствуйте!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

#### Streaming генерация
```http
POST /api/v1/llm/generate
Content-Type: application/json

{
  "prompt": "Расскажи историю",
  "stream": true
}
```

Ответ приходит в формате Server-Sent Events (SSE).

#### Проверка здоровья LLM
```http
GET /api/v1/llm/health
```

### Health Check

```http
GET /health
```

## Примеры использования

### Python (httpx)

```python
import httpx

async with httpx.AsyncClient() as client:
    # Создание агента
    response = await client.post(
        "http://localhost:8000/api/v1/agents",
        json={
            "name": "My Agent",
            "type": "llm",
            "capabilities": {},
        }
    )
    agent = response.json()
    
    # Генерация ответа
    response = await client.post(
        "http://localhost:8000/api/v1/llm/generate",
        json={
            "prompt": "Привет!",
            "temperature": 0.7,
        }
    )
    result = response.json()
    print(result["content"])
```

### cURL

```bash
# Создание агента
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "My Agent", "type": "llm"}'

# Генерация ответа
curl -X POST http://localhost:8000/api/v1/llm/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Привет!"}'
```

## Обработка ошибок

Все ошибки возвращаются в формате:

```json
{
  "error": "Error message",
  "detail": "Detailed error description",
  "timestamp": "2024-01-01T12:00:00"
}
```

HTTP статус коды:
- `200` - Успешно
- `201` - Создано
- `400` - Неверный запрос
- `404` - Не найдено
- `500` - Внутренняя ошибка сервера

## Примечания

- Все endpoints требуют валидных данных в формате JSON
- Временные метки возвращаются в формате ISO 8601
- Для streaming используйте `stream: true` в запросе генерации

