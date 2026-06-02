from __future__ import annotations

import json
import re
import subprocess

import emoji as emoji_lib
import grapheme

from .config import EmojiSuggestConfig, BackendMode
from .models import EmojiResult, EmojiSuggestion


def _official_matches(topic: str, config: EmojiSuggestConfig) -> list[EmojiSuggestion]:
    topic_words = {w.lower() for w in re.split(r"[\s,;]+", topic) if len(w) > 2}
    if not topic_words:
        topic_words = {topic.lower()}

    matches: list[tuple[str, str]] = []
    for char, data in emoji_lib.EMOJI_DATA.items():
        name = data.get("en", "").lower()
        aliases = " ".join(data.get("alias", [])).lower()
        if any(word in f"{name} {aliases}" for word in topic_words):
            matches.append((char, data.get("en", char)))

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


def _call_anthropic(prompt: str, config: EmojiSuggestConfig) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=config.anthropic_api_key or None)
    msg = client.messages.create(
        model=config.model,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def _call_ollama(prompt: str, config: EmojiSuggestConfig) -> str:
    import urllib.request
    payload = json.dumps({
        "model": config.ollama_model,
        "prompt": prompt,
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        f"{config.ollama_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["response"].strip()


def _parse_llm_response(raw: str) -> tuple[list[EmojiSuggestion], list[EmojiSuggestion]]:
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    # Some models add text before/after JSON — extract first {...} block
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        raw = m.group(0)
    data = json.loads(raw)
    creative = [EmojiSuggestion(**item) for item in data.get("creative", [])]
    from_subset = [EmojiSuggestion(**item) for item in data.get("from_subset", [])]
    return creative, from_subset


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
    prompt = _build_prompt(topic, active_subset, config)

    if config.backend == BackendMode.anthropic:
        raw = _call_anthropic(prompt, config)
    elif config.backend == BackendMode.ollama:
        raw = _call_ollama(prompt, config)
    else:
        raise ValueError(f"Unknown backend: {config.backend}")

    creative, from_subset = _parse_llm_response(raw)

    subset_graphemes = set(grapheme.graphemes("".join(active_subset)))
    from_subset = [s for s in from_subset if s.emoji in subset_graphemes]

    return EmojiResult(
        topic=topic,
        official=official,
        creative=creative,
        from_subset=from_subset,
    )
