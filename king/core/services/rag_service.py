"""
RAGService - интеграция с RAG-системами
Retrieval-Augmented Generation
"""

import logging
from typing import List, Optional

from king.core.ports.llm import AbstractLLMClient, Message
from king.core.ports.vector_store import AbstractVectorStore, SearchResult

logger = logging.getLogger(__name__)


class RAGService:
    """
    Сервис для RAG (Retrieval-Augmented Generation)
    Обеспечивает поиск релевантного контекста и инжекцию его в промпт
    """

    def __init__(
        self,
        llm_client: AbstractLLMClient,
        vector_store: AbstractVectorStore,
        collection: Optional[str] = None,
    ):
        """
        Инициализация RAG сервиса

        Args:
            llm_client: Клиент LLM для генерации embeddings
            vector_store: Векторное хранилище для поиска
            collection: Название коллекции в хранилище
        """
        self.llm_client = llm_client
        self.vector_store = vector_store
        self.collection = collection or "king_embeddings"

    async def add_documents(self, texts: List[str], metadata: Optional[List[dict]] = None) -> None:
        """
        Добавление документов в векторное хранилище

        Args:
            texts: Список текстов для добавления
            metadata: Метаданные для каждого документа

        Raises:
            ValueError: Если texts пуст или содержит невалидные данные
            NotImplementedError: Если embeddings не поддерживаются
        """
        # Валидация входных данных
        if not texts:
            raise ValueError("Список текстов не может быть пустым")
        
        if not isinstance(texts, list):
            raise ValueError("texts должен быть списком строк")
        
        if metadata is not None and len(metadata) != len(texts):
            logger.warning(
                f"Количество метаданных ({len(metadata)}) не совпадает с количеством текстов ({len(texts)})"
            )

        from king.core.ports.vector_store import Vector
        from uuid import uuid4

        vectors = []
        for i, text in enumerate(texts):
            # Валидация текста
            if not isinstance(text, str):
                raise ValueError(f"Текст на позиции {i} должен быть строкой, получен {type(text)}")
            
            if not text.strip():
                logger.warning(f"Пропущен пустой текст на позиции {i}")
                continue
            # Генерация embeddings для текста
            try:
                embedding = await self.llm_client.get_embeddings(text)
            except NotImplementedError:
                logger.error(
                    f"Embeddings не поддерживаются для {type(self.llm_client).__name__}. "
                    "RAG функциональность недоступна."
                )
                raise ValueError(
                    f"Embeddings не поддерживаются текущим LLM адаптером "
                    f"({type(self.llm_client).__name__}). "
                    "Для использования RAG необходим LLM адаптер с поддержкой embeddings."
                )
            except Exception as e:
                logger.error(f"Ошибка при генерации embeddings для текста {i}: {e}", exc_info=True)
                raise

            # Создание вектора с метаданными
            vector = Vector(
                id=str(uuid4()),
                vector=embedding,
                metadata={
                    "text": text,
                    **(metadata[i] if metadata and i < len(metadata) else {}),
                },
            )
            vectors.append(vector)

        # Добавление векторов в хранилище
        await self.vector_store.add_vectors(vectors, collection=self.collection)
        logger.info(f"Добавлено {len(vectors)} документов в коллекцию {self.collection}")

    async def search(
        self, query: str, top_k: int = 5, filter: Optional[dict] = None
    ) -> List[SearchResult]:
        """
        Поиск релевантных документов

        Args:
            query: Текст запроса
            top_k: Количество результатов
            filter: Фильтр по метаданным

        Returns:
            Список результатов поиска

        Raises:
            ValueError: Если query пуст или невалиден
            NotImplementedError: Если embeddings не поддерживаются
        """
        # Валидация входных данных
        if not query or not isinstance(query, str):
            raise ValueError("query должен быть непустой строкой")
        
        if not query.strip():
            raise ValueError("query не может быть пустой строкой")
        
        if top_k <= 0:
            raise ValueError("top_k должен быть положительным числом")
        
        # Генерация embeddings для запроса
        try:
            query_embedding = await self.llm_client.get_embeddings(query)
        except NotImplementedError:
            logger.error(
                f"Embeddings не поддерживаются для {type(self.llm_client).__name__}. "
                "RAG поиск недоступен."
            )
            raise ValueError(
                f"Embeddings не поддерживаются текущим LLM адаптером "
                f"({type(self.llm_client).__name__}). "
                "Для использования RAG необходим LLM адаптер с поддержкой embeddings."
            )
        except Exception as e:
            logger.error(f"Ошибка при генерации embeddings для запроса: {e}", exc_info=True)
            raise

        # Поиск в векторном хранилище
        results = await self.vector_store.search(
            query_vector=query_embedding,
            top_k=top_k,
            collection=self.collection,
            filter=filter,
        )

        logger.info(f"Найдено {len(results)} релевантных документов для запроса")
        return results

    async def generate_with_context(
        self,
        query: str,
        top_k: int = 5,
        context_template: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Генерация ответа с использованием найденного контекста

        Args:
            query: Текст запроса
            top_k: Количество релевантных документов для поиска
            context_template: Шаблон для форматирования контекста
            **kwargs: Дополнительные параметры для LLM

        Returns:
            Сгенерированный ответ

        Raises:
            ValueError: Если query невалиден или не найдено контекста
            NotImplementedError: Если embeddings не поддерживаются
        """
        try:
            # Поиск релевантного контекста
            search_results = await self.search(query, top_k=top_k)
        except (ValueError, NotImplementedError):
            # Пробрасываем известные ошибки
            raise
        except Exception as e:
            logger.error(f"Ошибка при поиске контекста: {e}", exc_info=True)
            raise ValueError(f"Не удалось найти релевантный контекст: {str(e)}") from e

        # Форматирование контекста
        try:
            if context_template:
                context = self._format_context_with_template(search_results, context_template)
            else:
                context = self._format_context_default(search_results)
        except Exception as e:
            logger.error(f"Ошибка при форматировании контекста: {e}", exc_info=True)
            raise ValueError(f"Не удалось отформатировать контекст: {str(e)}") from e

        # Создание промпта с контекстом
        enhanced_prompt = self._build_enhanced_prompt(query, context)

        # Генерация ответа через LLM
        try:
            response = await self.llm_client.generate(enhanced_prompt, **kwargs)
            return response.content
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа через LLM: {e}", exc_info=True)
            raise ValueError(f"Не удалось сгенерировать ответ: {str(e)}") from e

    def _format_context_default(self, results: List[SearchResult]) -> str:
        """
        Форматирование контекста по умолчанию

        Args:
            results: Результаты поиска

        Returns:
            Отформатированный контекст
        """
        if not results:
            return ""

        context_parts = []
        for i, result in enumerate(results, 1):
            text = result.metadata.get("text", "") if result.metadata else ""
            score = result.score
            context_parts.append(f"[{i}] (релевантность: {score:.2f})\n{text}")

        return "\n\n".join(context_parts)

    def _format_context_with_template(
        self, results: List[SearchResult], template: str
    ) -> str:
        """
        Форматирование контекста по шаблону

        Args:
            results: Результаты поиска
            template: Шаблон для форматирования

        Returns:
            Отформатированный контекст
        """
        # Простая реализация - можно расширить с использованием Jinja2
        context_texts = []
        for result in results:
            if result.metadata and "text" in result.metadata:
                context_texts.append(result.metadata["text"])

        return template.format(context="\n\n".join(context_texts))

    def _build_enhanced_prompt(self, query: str, context: str) -> str:
        """
        Построение промпта с контекстом

        Args:
            query: Запрос пользователя
            context: Найденный контекст

        Returns:
            Улучшенный промпт
        """
        if not context:
            return query

        return f"""Используй следующую информацию для ответа на вопрос:

{context}

Вопрос: {query}

Ответ:"""

    async def health_check(self) -> bool:
        """
        Проверка доступности RAG сервиса

        Returns:
            True если сервис доступен, False иначе
        """
        try:
            llm_ok = await self.llm_client.health_check()
            vector_store_ok = await self.vector_store.health_check()
            return llm_ok and vector_store_ok
        except Exception as e:
            logger.error(f"Ошибка при проверке здоровья RAG: {e}", exc_info=True)
            return False

