"""
GigaChat Adapter - реализация AbstractLLMClient для Sber GigaChat
"""

import asyncio
import logging
import time
from typing import AsyncIterator, List, Optional

import httpx

from pathlib import Path

from king.core.ports.llm import AbstractLLMClient, LLMResponse, Message

from .oauth import GigaChatOAuth2Client
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class GigaChatAdapter(AbstractLLMClient):
    """
    Адаптер для работы с Sber GigaChat API
    Реализует интерфейс AbstractLLMClient
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "https://gigachat.devices.sberbank.ru/api/v1",
        model: str = "GigaChat",
        scope: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        prompts_dir: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Инициализация GigaChat адаптера

        Args:
            client_id: Client ID для GigaChat
            client_secret: Client Secret для GigaChat
            base_url: Базовый URL API GigaChat
            model: Название модели
            scope: OAuth scope
            prompts_dir: Директория с шаблонами промптов
            max_retries: Максимальное количество повторов при ошибках
            retry_delay: Задержка между повторами (в секундах)
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Инициализация OAuth2 клиента
        self.oauth_client = GigaChatOAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
        )

        # Инициализация менеджера промптов
        self.prompt_manager = PromptManager(
            prompts_dir=Path(prompts_dir) if prompts_dir else None
        )

        # HTTP клиент
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

    async def generate(
        self,
        prompt: str,
        context: Optional[List[Message]] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse | AsyncIterator[LLMResponse]:
        """
        Генерация ответа от GigaChat

        Args:
            prompt: Текст промпта
            context: История диалога
            stream: Если True, возвращает AsyncIterator для streaming
            **kwargs: Дополнительные параметры (temperature, max_tokens и т.д.)

        Returns:
            LLMResponse или AsyncIterator[LLMResponse] при stream=True
        """
        if stream:
            return self.stream(prompt, context, **kwargs)

        # Форматирование сообщений для API
        messages = self.prompt_manager.format_messages(prompt, context)

        # Параметры запроса
        request_data = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
        }

        # Удаление None значений
        request_data = {k: v for k, v in request_data.items() if v is not None}

        # Выполнение запроса с retry логикой
        response_data = await self._request_with_retry(
            "POST",
            f"{self.base_url}/chat/completions",
            json=request_data,
        )

        # Парсинг ответа
        return self._parse_response(response_data)

    async def stream(
        self, prompt: str, context: Optional[List[Message]] = None, **kwargs
    ) -> AsyncIterator[LLMResponse]:
        """
        Streaming-генерация ответа

        Args:
            prompt: Текст промпта
            context: История диалога
            **kwargs: Дополнительные параметры

        Yields:
            LLMResponse с частичными ответами
        """
        # Форматирование сообщений
        messages = self.prompt_manager.format_messages(prompt, context)

        # Параметры запроса
        request_data = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "stream": True,
        }

        request_data = {k: v for k, v in request_data.items() if v is not None}

        # Получение токена
        access_token = await self.oauth_client.get_access_token()

        # Выполнение streaming запроса
        async with self._http_client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            json=request_data,
            headers={"Authorization": f"Bearer {access_token}"},
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.strip():
                    continue

                if line.startswith("data: "):
                    data_str = line[6:]  # Убираем "data: "
                    if data_str == "[DONE]":
                        break

                    try:
                        import json

                        chunk_data = json.loads(data_str)
                        choices = chunk_data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield LLMResponse(
                                    content=content,
                                    model=chunk_data.get("model"),
                                    metadata={"chunk": True},
                                )
                    except Exception as e:
                        logger.warning(f"Ошибка при парсинге streaming chunk: {e}")

    async def get_embeddings(self, text: str) -> List[float]:
        """
        Получение embeddings для текста

        Args:
            text: Текст для векторизации

        Returns:
            Список чисел (вектор embeddings)

        Note:
            GigaChat может не поддерживать embeddings напрямую
            В этом случае возвращается заглушка
        """
        # GigaChat может не иметь прямого API для embeddings
        # Здесь можно использовать альтернативный метод или вернуть ошибку
        logger.warning("GigaChat может не поддерживать embeddings напрямую")
        raise NotImplementedError("GigaChat embeddings не реализованы")

    async def health_check(self) -> bool:
        """
        Проверка доступности GigaChat API

        Returns:
            True если API доступен, False иначе
        """
        try:
            # Попытка получить токен
            await self.oauth_client.get_access_token()
            return True
        except Exception as e:
            logger.error(f"GigaChat health check failed: {e}", exc_info=True)
            return False

    async def _request_with_retry(
        self, method: str, url: str, **kwargs
    ) -> dict:
        """
        Выполнение HTTP запроса с retry логикой и exponential backoff

        Args:
            method: HTTP метод
            url: URL запроса
            **kwargs: Дополнительные параметры для httpx

        Returns:
            JSON ответ

        Raises:
            httpx.HTTPStatusError: При ошибке HTTP запроса после всех повторов
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                # Получение токена
                access_token = await self.oauth_client.get_access_token()

                # Добавление заголовка авторизации
                headers = kwargs.get("headers", {})
                headers["Authorization"] = f"Bearer {access_token}"
                kwargs["headers"] = headers

                # Выполнение запроса
                response = await self._http_client.request(method, url, **kwargs)

                # Обработка rate limit
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", self.retry_delay * (2 ** attempt)))
                    logger.warning(f"Rate limit, ожидание {retry_after} секунд")
                    await asyncio.sleep(retry_after)
                    continue

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code == 401:
                    # Токен истек, обновляем и повторяем
                    logger.info("Токен истек, обновляем...")
                    await self.oauth_client.refresh_token()
                    continue
                elif e.response.status_code >= 500:
                    # Серверная ошибка, повторяем
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Серверная ошибка, повтор через {delay} секунд (попытка {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Клиентская ошибка, не повторяем
                    raise

            except Exception as e:
                last_exception = e
                delay = self.retry_delay * (2 ** attempt)
                logger.warning(f"Ошибка запроса, повтор через {delay} секунд (попытка {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(delay)
                else:
                    raise

        # Если все попытки исчерпаны
        if last_exception:
            raise last_exception

        raise Exception("Не удалось выполнить запрос после всех попыток")

    def _parse_response(self, response_data: dict) -> LLMResponse:
        """
        Парсинг ответа от GigaChat API

        Args:
            response_data: JSON ответ от API

        Returns:
            LLMResponse
        """
        choices = response_data.get("choices", [])
        if not choices:
            raise ValueError("Пустой ответ от GigaChat API")

        message = choices[0].get("message", {})
        content = message.get("content", "")

        usage = response_data.get("usage", {})
        tokens_used = usage.get("total_tokens")

        return LLMResponse(
            content=content,
            model=response_data.get("model", self.model),
            tokens_used=tokens_used,
            metadata={
                "finish_reason": choices[0].get("finish_reason"),
                "usage": usage,
            },
        )

    async def close(self) -> None:
        """Закрытие ресурсов"""
        await self.oauth_client.close()
        await self._http_client.aclose()

    def __del__(self):
        """Деструктор"""
        try:
            if hasattr(self, "_http_client"):
                asyncio.create_task(self._http_client.aclose())
        except Exception:
            pass

