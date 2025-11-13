# Messaging адаптеры

Адаптеры для работы с системами обмена сообщениями (Kafka, RabbitMQ).

## KafkaAdapter

Адаптер для Apache Kafka с поддержкой асинхронного и синхронного режимов.

### Использование

```python
from king.adapters.messaging import KafkaAdapter

# Создание адаптера
kafka = KafkaAdapter(
    bootstrap_servers=["localhost:9092"],
    topic_prefix="king",
    consumer_group="king-consumer"
)

# Публикация сообщения
await kafka.publish("events", {"type": "test", "data": "hello"})

# Потребление сообщений
async for message in kafka.consume("events"):
    print(message)
```

### Особенности

- Поддержка `aiokafka` (асинхронный, рекомендуется)
- Fallback на `kafka-python` (синхронный)
- Автоматическое создание топиков
- Consumer groups для балансировки нагрузки

## RabbitMQAdapter

Адаптер для RabbitMQ с поддержкой различных типов exchange.

### Использование

```python
from king.adapters.messaging import RabbitMQAdapter

# Создание адаптера
rabbitmq = RabbitMQAdapter(
    url="amqp://guest:guest@localhost:5672/",
    exchange_name="king",
    exchange_type="topic"
)

# Публикация сообщения
await rabbitmq.publish("events.test", {"type": "test", "data": "hello"})

# Потребление сообщений
async for message in rabbitmq.consume("events.test"):
    print(message)
```

### Особенности

- Асинхронная работа через `aio-pika`
- Поддержка различных типов exchange (direct, topic, fanout)
- Durable queues для надежности
- Автоматическое создание очередей

## MessagingEventBusAdapter

Адаптер для интеграции доменного EventBus с внешними messaging системами.

### Использование

```python
from king.adapters.messaging import MessagingEventBusAdapter
from king.core.domain import EventBus
from king.adapters.messaging import KafkaAdapter

# Создание адаптера
event_bus = EventBus()
kafka = KafkaAdapter()
adapter = MessagingEventBusAdapter(event_bus, kafka)

# Запуск
await adapter.start()

# События автоматически публикуются в Kafka
```

## Конфигурация

Настройки через переменные окружения:

```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=king
KAFKA_CONSUMER_GROUP=king-consumer

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

## Зависимости

- `aiokafka>=0.10.0` (рекомендуется для асинхронной работы)
- `kafka-python>=2.0.2` (fallback)
- `aio-pika>=9.2.0` (для RabbitMQ)

