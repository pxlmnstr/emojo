# emoji-suggest

Suggest emojis for any topic — in three categories:

1. **Official** — emojis whose Unicode name/description matches your topic
2. **Creative** — emojis commonly used for this topic despite a different official meaning
3. **From subset** — best picks from a custom or default set of emojis

Requires an Anthropic API key for categories 2 and 3.

## Installation

```bash
pip install emoji-suggest
# or with YAML config support:
pip install "emoji-suggest[yaml-config]"
```

## Setup

Set your API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Or create `~/.config/emoji-suggest/config.yaml`:

```yaml
anthropic_api_key: sk-ant-...
model: claude-haiku-4-5-20251001   # optional, this is the default
```

## CLI usage

```bash
emoji-suggest "Geschwindigkeit"
emoji-suggest "download" --subset "⬇️📥💾🔽"
emoji-suggest "Feuer" --json
```

## Python usage

```python
from emoji_suggest import suggest, EmojiSuggestConfig

result = suggest("Geschwindigkeit")
print(result.official)    # list[EmojiSuggestion]
print(result.creative)
print(result.from_subset)

# Custom config
config = EmojiSuggestConfig(model="claude-sonnet-4-6")
result = suggest("fire", subset=["🔥", "♨️", "💥"], config=config)
```

## Publishing to PyPI

1. Build: `python -m build`
2. Upload: `twine upload dist/*`
   - You need a PyPI account and `pip install build twine`
   - Set `__version__` in `pyproject.toml` before each release

## GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/emoji-suggest.git
git push -u origin main
```
