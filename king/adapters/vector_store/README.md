# Vector Store адаптеры

Адаптеры для работы с векторными хранилищами (Qdrant, Chroma) для поддержки RAG.

## QdrantAdapter

Адаптер для Qdrant - высокопроизводительного векторного хранилища.

### Использование

```python
from king.adapters.vector_store import QdrantAdapter

# Создание адаптера
qdrant = QdrantAdapter(
    url="http://localhost:6333",
    collection_name="king_vectors",
    vector_size=1536
)

# Добавление векторов
from king.core.ports.vector_store import Vector
vectors = [
    Vector(
        id="1",
        vector=[0.1, 0.2, ...],
        metadata={"text": "Пример текста"}
    )
]
await qdrant.add_vectors(vectors)

# Поиск
results = await qdrant.search(
    query_vector=[0.1, 0.2, ...],
    top_k=5
)
```

### Особенности

- Поддержка фильтрации по метаданным
- Автоматическое создание коллекций
- Косинусное расстояние для поиска
- Health check для мониторинга

## ChromaAdapter

Адаптер для Chroma - легковесного векторного хранилища.

### Использование

```python
from king.adapters.vector_store import ChromaAdapter

# Создание адаптера (in-memory)
chroma = ChromaAdapter(
    collection_name="king_vectors"
)

# Или с персистентностью
chroma = ChromaAdapter(
    persist_directory="./chroma_db",
    collection_name="king_vectors"
)

# Добавление векторов
from king.core.ports.vector_store import Vector
vectors = [
    Vector(
        id="1",
        vector=[0.1, 0.2, ...],
        metadata={"text": "Пример текста"}
    )
]
await chroma.add_vectors(vectors)

# Поиск
results = await chroma.search(
    query_vector=[0.1, 0.2, ...],
    top_k=5
)
```

### Особенности

- In-memory или персистентный режим
- Автоматическое создание коллекций
- Косинусное расстояние для поиска
- Health check для мониторинга

## Интеграция с RAGService

Оба адаптера полностью совместимы с `RAGService`:

```python
from king.core.services.rag_service import RAGService
from king.adapters.vector_store import QdrantAdapter
from king.adapters.llm.gigachat import GigaChatAdapter

# Создание компонентов
llm = GigaChatAdapter(...)
vector_store = QdrantAdapter(...)

# Создание RAG сервиса
rag = RAGService(llm_client=llm, vector_store=vector_store)

# Добавление документов
await rag.add_documents(
    texts=["Документ 1", "Документ 2"],
    metadata=[{"source": "doc1"}, {"source": "doc2"}]
)

# Генерация с контекстом
response = await rag.generate_with_context(
    query="Что такое RAG?",
    top_k=3
)
```

## Конфигурация

Настройки через переменные окружения:

```bash
# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_api_key
QDRANT_COLLECTION=king_vectors

# Chroma
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION=king_vectors
```

## Зависимости

- `qdrant-client>=1.7.0` (для Qdrant)
- `chromadb>=0.4.0` (для Chroma)

