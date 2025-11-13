"""
Chroma адаптер для векторного хранилища
"""

import logging
from typing import List, Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

from king.core.ports.vector_store import AbstractVectorStore, SearchResult, Vector

logger = logging.getLogger(__name__)


class ChromaAdapter(AbstractVectorStore):
    """
    Адаптер для Chroma векторного хранилища
    Реализует интерфейс AbstractVectorStore
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "king_vectors",
        host: str = "localhost",
        port: int = 8000,
    ):
        """
        Инициализация Chroma адаптера

        Args:
            persist_directory: Директория для персистентности (None = in-memory)
            collection_name: Название коллекции
            host: Хост Chroma сервера (если используется клиент)
            port: Порт Chroma сервера (если используется клиент)
        """
        if not CHROMA_AVAILABLE:
            raise ImportError(
                "chromadb не установлен. Установите: pip install chromadb"
            )

        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Создание клиента
        if persist_directory:
            # Персистентный режим
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            # In-memory режим
            self.client = chromadb.Client()

        # Получение или создание коллекции
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},  # Косинусное расстояние
            )
            logger.info(f"Коллекция {collection_name} готова")
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

        # Получение коллекции
        if collection_name != self.collection_name:
            try:
                coll = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception:
                coll = self.collection
        else:
            coll = self.collection

        try:
            # Chroma ожидает метаданные в плоском формате
            # Преобразуем вложенные словари в строки
            flat_metadata = []
            for vector in vectors:
                flat_meta = {}
                for key, value in vector.metadata.items():
                    # Chroma поддерживает только строки, числа и списки
                    if isinstance(value, (str, int, float, list)):
                        flat_meta[key] = value
                    else:
                        flat_meta[key] = str(value)
                flat_metadata.append(flat_meta)

            coll.add(
                ids=[v.id for v in vectors],
                embeddings=[v.vector for v in vectors],
                metadatas=flat_metadata,
            )
            logger.debug(f"Добавлено {len(vectors)} векторов в коллекцию {collection_name}")
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

        # Получение коллекции
        if collection_name != self.collection_name:
            try:
                coll = self.client.get_collection(name=collection_name)
            except Exception:
                coll = self.collection
        else:
            coll = self.collection

        try:
            # Chroma использует where для фильтрации
            where = filter if filter else None

            results = coll.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where,
            )

            # Преобразование результатов
            search_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i, vector_id in enumerate(results["ids"][0]):
                    score = 1.0 - results["distances"][0][i] if "distances" in results else 1.0
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}

                    search_results.append(
                        SearchResult(
                            id=vector_id,
                            score=score,
                            vector=None,  # Chroma не возвращает векторы по умолчанию
                            metadata=metadata or {},
                        )
                    )

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

        # Получение коллекции
        if collection_name != self.collection_name:
            try:
                coll = self.client.get_collection(name=collection_name)
            except Exception:
                coll = self.collection
        else:
            coll = self.collection

        try:
            coll.delete(ids=ids)
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
            dimension: Размерность векторов (игнорируется для Chroma)
            **kwargs: Дополнительные параметры
        """
        try:
            self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
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
            # Простая проверка - попытка получить список коллекций
            collections = self.client.list_collections()
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке здоровья Chroma: {e}", exc_info=True)
            return False

