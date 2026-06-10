# emojo

Suggest emojis for any topic — in three categories:

1. **Official** — emojis whose Unicode name/description matches your topic
2. **Creative** — emojis commonly used for this topic despite a different official meaning
3. **From subset** — best picks from a custom or default set of emojis

Categories 2 and 3 are produced by an LLM. Three backends are available:

| Backend | Cost | Setup |
|---------|------|-------|
| `claude-cli` *(default)* | **Free with a Claude Pro/Max subscription** — no API credits | Install the Claude Code CLI and log in once |
| `anthropic` | Pay-as-you-go API credits | Anthropic API key |
| `ollama` | Free, fully local | A running Ollama server |

## Installation

```bash
pip install emojo
# or with YAML config support:
pip install "emojo[yaml-config]"
# for the anthropic backend:
pip install "emojo[anthropic]"
```

## Setup

### Default: `claude-cli` (uses your Claude subscription, no API credits)

Install the official Claude Code CLI and log in once with your Pro/Max account:

```bash
npm install -g @anthropic-ai/claude-code
claude            # run once, then use /login
```

That's it — `emojo` will find `claude` on your `PATH` and reuse that
login. No API key, no per-request charges (it counts against your normal
subscription usage).

> Note: the `claude` binary bundled *inside* the Claude desktop app cannot be
> used — it only authenticates when launched by the desktop app itself. You need
> the standalone CLI from `npm`.

### Alternative: `anthropic` (API key)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
emojo "Feuer" --backend anthropic
```

### Alternative: `ollama` (local)

```bash
ollama serve
emojo "Feuer" --backend ollama --model llama3.2
```

### Config file

Create `~/.config/emojo/config.yaml` (needs `[yaml-config]` extra):

```yaml
backend: claude-cli            # claude-cli (default) | anthropic | ollama
# claude_cli_path: /opt/homebrew/bin/claude   # optional, auto-detected from PATH
# claude_cli_model: claude-haiku-4-5          # optional, empty = CLI default
# anthropic_api_key: sk-ant-...               # only for backend: anthropic
# ollama_model: llama3.2                      # only for backend: ollama

# Languages searched for official (category 1) emoji names/keywords.
# Any subset of: en es ja ko pt it fr de fa id zh ru tr ar
official_languages: [en, de]
# Language for the "reason" texts in the output.
response_language: de
```

## CLI usage

```bash
emojo "Geschwindigkeit"
emojo "download" --subset "⬇️📥💾🔽"
emojo "Feuer" --json
```

## Python usage

```python
from emojo import suggest, EmojoConfig

result = suggest("Geschwindigkeit")
print(result.official)    # list[EmojiSuggestion]
print(result.creative)
print(result.from_subset)

# Custom config — pick a backend explicitly
from emojo import BackendMode
config = EmojoConfig(backend=BackendMode.claude_cli)
result = suggest("fire", subset=["🔥", "♨️", "💥"], config=config)
```

## Publishing to PyPI

1. Build: `python -m build`
2. Upload: `twine upload dist/*`
   - You need a PyPI account and `pip install build twine`
   - Set `__version__` in `pyproject.toml` before each release

## GitHub

```bash
git remote add origin https://github.com/pxlmnstr/emojo.git
git push -u origin main
```
