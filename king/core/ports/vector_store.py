"""
Интерфейс для векторных хранилищ (Qdrant, Chroma и т.д.)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Vector:
    """Вектор с метаданными"""
    id: str
    vector: List[float]
    metadata: Dict[str, Any]


@dataclass
class SearchResult:
    """Результат поиска в векторном хранилище"""
    id: str
    score: float
    vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None


class AbstractVectorStore(ABC):
    """
    Унифицированный интерфейс для векторных хранилищ
    """
    
    @abstractmethod
    async def add_vectors(
        self,
        vectors: List[Vector],
        collection: Optional[str] = None
    ) -> None:
        """
        Добавление векторов в хранилище
        
        Args:
            vectors: Список векторов для добавления
            collection: Название коллекции (опционально)
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        collection: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Поиск похожих векторов
        
        Args:
            query_vector: Вектор запроса
            top_k: Количество результатов
            collection: Название коллекции
            filter: Фильтр по метаданным
        
        Returns:
            Список результатов поиска, отсортированный по релевантности
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        ids: List[str],
        collection: Optional[str] = None
    ) -> None:
        """
        Удаление векторов по ID
        
        Args:
            ids: Список ID для удаления
            collection: Название коллекции
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Проверка доступности хранилища
        
        Returns:
            True если хранилище доступно, False иначе
        """
        pass

