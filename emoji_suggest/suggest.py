from __future__ import annotations

import json
import re

import emoji as emoji_lib
import grapheme

from .config import EmojiSuggestConfig
from .models import EmojiResult, EmojiSuggestion


def _official_matches(topic: str, config: EmojiSuggestConfig) -> list[EmojiSuggestion]:
    """Return emojis whose Unicode name or CLDR keywords contain the topic words."""
    topic_words = {w.lower() for w in re.split(r"[\s,;]+", topic) if len(w) > 2}
    if not topic_words:
        topic_words = {topic.lower()}

    matches: list[tuple[str, str]] = []
    for char, data in emoji_lib.EMOJI_DATA.items():
        name = data.get("en", "").lower()
        aliases = " ".join(data.get("alias", [])).lower()
        combined = f"{name} {aliases}"
        if any(word in combined for word in topic_words):
            matches.append((char, data.get("en", char)))

    # Sort by how many words match, descending
    def score(item: tuple[str, str]) -> int:
        return sum(1 for w in topic_words if w in item[1].lower())

    matches.sort(key=score, reverse=True)
    return [
        EmojiSuggestion(emoji=char, reason=f"Official name: {name}")
        for char, name in matches[: config.max_official]
    ]


def _build_prompt(topic: str, subset: list[str], config: EmojiSuggestConfig) -> str:
    subset_str = " ".join(subset)
    return f"""You are an emoji expert. Given a topic, return a JSON object with two keys:

"creative": A list of up to {config.max_creative} emojis that people commonly use to represent "{topic}", even if the emoji officially means something else. Include only the emoji character and a short reason.

"from_subset": From this specific set of emojis: {subset_str}
Pick up to {config.max_subset} that could best represent "{topic}". Only pick from that exact list; if none fit, return an empty list.

Respond ONLY with valid JSON, no markdown, no explanation. Format:
{{
  "creative": [{{"emoji": "🔥", "reason": "used to express intensity or popularity"}}],
  "from_subset": [{{"emoji": "➡️", "reason": "direction / forward motion"}}]
}}

Topic: {topic}"""


def suggest(
    topic: str,
    subset: list[str] | None = None,
    config: EmojiSuggestConfig | None = None,
) -> EmojiResult:
    """Return emoji suggestions for *topic* in three categories."""
    if config is None:
        config = EmojiSuggestConfig()

    active_subset = subset if subset is not None else config.default_subset

    official = _official_matches(topic, config)

    # Call Claude for creative + subset suggestions
    import anthropic

    client = anthropic.Anthropic(api_key=config.anthropic_api_key or None)
    prompt = _build_prompt(topic, active_subset, config)

    message = client.messages.create(
        model=config.model,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    data = json.loads(raw)

    creative = [EmojiSuggestion(**item) for item in data.get("creative", [])]
    from_subset = [EmojiSuggestion(**item) for item in data.get("from_subset", [])]

    # Validate that from_subset emojis are actually in the subset
    subset_graphemes = set(grapheme.graphemes("".join(active_subset)))
    from_subset = [s for s in from_subset if s.emoji in subset_graphemes]

    return EmojiResult(
        topic=topic,
        official=official,
        creative=creative,
        from_subset=from_subset,
    )
