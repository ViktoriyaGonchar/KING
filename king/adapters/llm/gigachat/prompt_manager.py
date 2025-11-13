"""
Управление промптами для GigaChat
Загрузка и рендеринг шаблонов через Jinja2
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import jinja2
import yaml

from king.core.ports.llm import Message

logger = logging.getLogger(__name__)


class PromptManager:
    """
    Менеджер промптов для GigaChat
    Загружает шаблоны из YAML файлов и рендерит их через Jinja2
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Инициализация менеджера промптов

        Args:
            prompts_dir: Директория с шаблонами промптов
        """
        if prompts_dir is None:
            # По умолчанию ищем в config/prompts/gigachat/
            base_dir = Path(__file__).parent.parent.parent.parent.parent
            prompts_dir = base_dir / "config" / "prompts" / "gigachat"

        self.prompts_dir = Path(prompts_dir)
        self._templates: Dict[str, jinja2.Template] = {}
        self._jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.prompts_dir)),
            autoescape=False,
        )

        self._load_templates()

    def _load_templates(self) -> None:
        """Загрузка шаблонов из YAML файлов"""
        if not self.prompts_dir.exists():
            logger.warning(f"Директория промптов не найдена: {self.prompts_dir}")
            return

        for yaml_file in self.prompts_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                # Загрузка каждого шаблона из YAML
                for template_name, template_content in data.items():
                    if isinstance(template_content, str):
                        template_key = f"{yaml_file.stem}.{template_name}"
                        self._templates[template_key] = self._jinja_env.from_string(
                            template_content
                        )
                        logger.debug(f"Загружен шаблон: {template_key}")

            except Exception as e:
                logger.error(f"Ошибка при загрузке шаблона {yaml_file}: {e}", exc_info=True)

    def render_prompt(
        self,
        user_message: str,
        context: Optional[List[Message]] = None,
        template_name: str = "default.full_prompt",
        **kwargs
    ) -> str:
        """
        Рендеринг промпта из шаблона

        Args:
            user_message: Сообщение пользователя
            context: История диалога
            template_name: Имя шаблона (например, "default.full_prompt")
            **kwargs: Дополнительные переменные для шаблона

        Returns:
            Отрендеренный промпт
        """
        # Получение шаблона
        template = self._templates.get(template_name)
        if not template:
            # Если шаблон не найден, используем простой формат
            logger.warning(f"Шаблон {template_name} не найден, используется простой формат")
            return self._simple_format(user_message, context)

        # Подготовка контекста для шаблона
        template_vars = {
            "user_message": user_message,
            "context": context or [],
            **kwargs,
        }

        # Рендеринг
        try:
            return template.render(**template_vars).strip()
        except Exception as e:
            logger.error(f"Ошибка при рендеринге шаблона {template_name}: {e}", exc_info=True)
            return self._simple_format(user_message, context)

    def _simple_format(self, user_message: str, context: Optional[List[Message]]) -> str:
        """
        Простое форматирование без шаблона

        Args:
            user_message: Сообщение пользователя
            context: История диалога

        Returns:
            Отформатированный промпт
        """
        if not context:
            return user_message

        context_str = "\n".join([f"{msg.role}: {msg.content}" for msg in context])
        return f"{context_str}\nuser: {user_message}"

    def format_messages(
        self, user_message: str, context: Optional[List[Message]] = None
    ) -> List[Dict[str, str]]:
        """
        Форматирование сообщений для GigaChat API

        Args:
            user_message: Сообщение пользователя
            context: История диалога

        Returns:
            Список сообщений в формате GigaChat API
        """
        messages = []

        # Добавление системного промпта (если есть)
        system_template = self._templates.get("default.system")
        if system_template:
            try:
                system_message = system_template.render().strip()
                if system_message:
                    messages.append({"role": "system", "content": system_message})
            except Exception:
                pass

        # Добавление истории диалога
        if context:
            for msg in context:
                messages.append({"role": msg.role, "content": msg.content})

        # Добавление текущего сообщения пользователя
        messages.append({"role": "user", "content": user_message})

        return messages

