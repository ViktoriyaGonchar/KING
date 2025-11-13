"""
LLM-адаптеры для различных провайдеров
"""

from king.adapters.llm.gigachat import GigaChatAdapter, GigaChatOAuth2Client, PromptManager

# Импорты будут добавлены по мере реализации адаптеров
# from king.adapters.llm.openai import OpenAIAdapter
# from king.adapters.llm.yandex_gpt import YandexGPTAdapter

__all__ = [
    "GigaChatAdapter",
    "GigaChatOAuth2Client",
    "PromptManager",
    # "OpenAIAdapter",
    # "YandexGPTAdapter",
]

