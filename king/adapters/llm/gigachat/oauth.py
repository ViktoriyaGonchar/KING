"""
OAuth2 клиент для GigaChat
"""

import asyncio
import logging
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class GigaChatOAuth2Client:
    """
    OAuth2 клиент для получения access_token от GigaChat
    Использует client_credentials flow
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scope: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        token_url: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
    ):
        """
        Инициализация OAuth2 клиента

        Args:
            client_id: Client ID для GigaChat
            client_secret: Client Secret для GigaChat
            scope: OAuth scope
            token_url: URL для получения токена
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.token_url = token_url

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._lock = asyncio.Lock()
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Получение access_token с автоматическим обновлением

        Args:
            force_refresh: Принудительное обновление токена

        Returns:
            Access token
        """
        async with self._lock:
            # Проверка, нужен ли новый токен
            if not force_refresh and self._access_token and time.time() < self._token_expires_at:
                return self._access_token

            # Получение нового токена
            token_data = await self._request_token()
            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 1800)  # По умолчанию 30 минут

            # Устанавливаем время истечения с запасом в 60 секунд
            self._token_expires_at = time.time() + expires_in - 60

            logger.info("Получен новый access_token для GigaChat")
            return self._access_token

    async def _request_token(self) -> dict:
        """
        Запрос токена через OAuth2

        Returns:
            Данные токена

        Raises:
            httpx.HTTPStatusError: При ошибке HTTP запроса
        """
        data = {
            "scope": self.scope,
        }

        auth = (self.client_id, self.client_secret)

        try:
            response = await self._http_client.post(
                self.token_url,
                data=data,
                auth=auth,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Ошибка при получении токена: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении токена: {e}", exc_info=True)
            raise

    async def refresh_token(self) -> str:
        """
        Принудительное обновление токена

        Returns:
            Новый access token
        """
        return await self.get_access_token(force_refresh=True)

    async def close(self) -> None:
        """Закрытие HTTP клиента"""
        await self._http_client.aclose()

    def __del__(self):
        """Деструктор для закрытия клиента"""
        try:
            if hasattr(self, "_http_client"):
                asyncio.create_task(self._http_client.aclose())
        except Exception:
            pass

