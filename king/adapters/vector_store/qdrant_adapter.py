"""
Qdrant адаптер для векторного хранилища
"""

import logging
from typing import List, Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from king.core.ports.vector_store import AbstractVectorStore, SearchResult, Vector

logger = logging.getLogger(__name__)


class QdrantAdapter(AbstractVectorStore):
    """
    Адаптер для Qdrant векторного хранилища
    Реализует интерфейс AbstractVectorStore
    """

    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: Optional[str] = None,
        collection_name: str = "king_vectors",
        vector_size: int = 1536,  # Размер по умолчанию для OpenAI embeddings
    ):
        """
        Инициализация Qdrant адаптера

        Args:
            url: URL Qdrant сервера
            api_key: API ключ (опционально)
            collection_name: Название коллекции
            vector_size: Размер векторов
        """
        if not QDRANT_AVAILABLE:
            raise ImportError(
                "qdrant-client не установлен. Установите: pip install qdrant-client"
            )

        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self.vector_size = vector_size

        # Создание клиента
        self.client = QdrantClient(url=url, api_key=api_key)

        # Создание коллекции если не существует
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Создание коллекции если не существует"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        "size": self.vector_size,
                        "distance": Distance.COSINE,
                    },
                )
                logger.info(f"Создана коллекция {self.collection_name}")
        except Exception as e:
            logger.error(f"Ошибка при создании коллекции: {e}", exc_info=True)
            raise

    async def add_vectors(
        self,
        vectors: List[Vector],
        collection: Optional[str] = None,
    ) -> None:
        """
        Добавление векторов в хранилище

        Args:
            vectors: Список векторов с метаданными
            collection: Название коллекции (игнорируется, используется self.collection_name)
        """
        collection_name = collection or self.collection_name

        try:
            points = [
                PointStruct(
                    id=vector.id,
                    vector=vector.vector,
                    payload=vector.metadata,
                )
                for vector in vectors
            ]

            self.client.upsert(
                collection_name=collection_name,
                points=points,
            )
            logger.debug(f"Добавлено {len(points)} векторов в коллекцию {collection_name}")
        except Exception as e:
            logger.error(f"Ошибка при добавлении векторов: {e}", exc_info=True)
            raise

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        collection: Optional[str] = None,
        filter: Optional[dict] = None,
    ) -> List[SearchResult]:
        """
        Поиск похожих векторов

        Args:
            query_vector: Вектор запроса
            top_k: Количество результатов
            collection: Название коллекции (игнорируется, используется self.collection_name)
            filter: Фильтр по метаданным (опционально)

        Returns:
            Список результатов поиска
        """
        collection_name = collection or self.collection_name

        if len(query_vector) != self.vector_size:
            raise ValueError(
                f"Размер вектора запроса ({len(query_vector)}) не совпадает с размером векторов коллекции ({self.vector_size})"
            )

        try:
            # Построение фильтра
            qdrant_filter = None
            if filter:
                conditions = []
                for key, value in filter.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value),
                        )
                    )
                if conditions:
                    qdrant_filter = Filter(must=conditions)

            # Поиск
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=qdrant_filter,
            )

            # Преобразование результатов
            search_results = [
                SearchResult(
                    id=str(point.id),
                    score=point.score,
                    vector=None,  # Qdrant не возвращает векторы по умолчанию
                    metadata=point.payload or {},
                )
                for point in results
            ]

            logger.debug(f"Найдено {len(search_results)} результатов")
            return search_results
        except Exception as e:
            logger.error(f"Ошибка при поиске векторов: {e}", exc_info=True)
            raise

    async def delete(self, ids: List[str], collection: Optional[str] = None) -> None:
        """
        Удаление векторов по ID

        Args:
            ids: Список ID для удаления
            collection: Название коллекции (игнорируется, используется self.collection_name)
        """
        collection_name = collection or self.collection_name

        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=ids,
            )
            logger.debug(f"Удалено {len(ids)} векторов из коллекции {collection_name}")
        except Exception as e:
            logger.error(f"Ошибка при удалении векторов: {e}", exc_info=True)
            raise

    async def create_collection(
        self,
        name: str,
        dimension: int,
        **kwargs
    ) -> None:
        """
        Создание новой коллекции

        Args:
            name: Название коллекции
            dimension: Размерность векторов
            **kwargs: Дополнительные параметры
        """
        try:
            self.client.create_collection(
                collection_name=name,
                vectors_config={
                    "size": dimension,
                    "distance": Distance.COSINE,
                },
            )
            logger.info(f"Создана коллекция {name}")
        except Exception as e:
            logger.error(f"Ошибка при создании коллекции: {e}", exc_info=True)
            raise

    async def health_check(self) -> bool:
        """
        Проверка доступности хранилища

        Returns:
            True если хранилище доступно, False иначе
        """
        try:
            collections = self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке здоровья Qdrant: {e}", exc_info=True)
            return False

