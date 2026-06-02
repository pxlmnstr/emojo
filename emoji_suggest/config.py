from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, Tuple, Type

import grapheme
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

try:
    from pydantic_settings import YamlConfigSettingsSource
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

_SUBSET_STR = (
    "⬇️🔢➡️⤵️🔂2️⃣🔠🔣3️⃣↩️7️⃣🚻0️⃣↗️⬆️4️⃣🆒⏺️⏹️🆓⏸️🎦*️⃣⬅️📶🈁🆗◀️🆖"
    "🔽🔼⏯️▶️#️⃣9️⃣5️⃣⤴️🔟⏩🆙🆕1️⃣6️⃣8️⃣🔡🔤ℹ️↔️↕️⏫🔃⏪↘️↙️🚮↖️⏬↪️🔀⏮️🔁🔄⏭️"
)
DEFAULT_SUBSET: list[str] = [e for e in grapheme.graphemes(_SUBSET_STR) if e.strip()]

_CONFIG_FILE = str(Path.home() / ".config" / "emoji-suggest" / "config.yaml")


class EmojiSuggestConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EMOJI_SUGGEST_",
        env_file=".env",
        extra="ignore",
    )

    # Read ANTHROPIC_API_KEY from env directly (no prefix)
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key",
    )
    model: str = Field(
        default="claude-haiku-4-5-20251001",
        description="Claude model to use",
    )
    default_subset: list[str] = Field(
        default_factory=lambda: DEFAULT_SUBSET,
        description="Default emoji subset for part 3 of the result",
    )
    max_official: int = Field(default=2)
    max_creative: int = Field(default=5)
    max_subset: int = Field(default=5)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        sources: list[Any] = [init_settings, env_settings, dotenv_settings]
        if _HAS_YAML:
            from pydantic_settings import YamlConfigSettingsSource
            sources.append(YamlConfigSettingsSource(settings_cls, yaml_file=_CONFIG_FILE))
        return tuple(sources)

    def model_post_init(self, __context: Any) -> None:
        # Also pick up bare ANTHROPIC_API_KEY (without prefix) from env
        import os
        if not self.anthropic_api_key:
            self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
