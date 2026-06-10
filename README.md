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

A bare topic runs the query (no subcommand needed):

```bash
emojo "Geschwindigkeit"
emojo "download" --subset "⬇️📥💾🔽"
emojo "Feuer" --json
```

While the query runs, an animated `Searching ....` indicator is shown on
stderr (suppressed when output is piped or `--json` is used).

### Query options (override the config file per call)

| Option | Short | Meaning |
|--------|-------|---------|
| `--subset TEXT` | `-s` | Use this emoji set for category 3 instead of the default |
| `--backend NAME` | `-b` | `claude-cli` \| `anthropic` \| `ollama` |
| `--model NAME` | `-m` | Model name for the chosen backend |
| `--languages a,b` | `-l` | Languages for the official search, e.g. `en,de` |
| `--response-language X` | `-r` | Language of the reason texts, e.g. `de` |
| `--max-official N` / `--max-creative N` / `--max-subset N` | | Result caps per category |
| `--json` | | Print the raw result as JSON |

```bash
emojo "Recycling" --languages en,de --response-language de
emojo "fire" --backend ollama --model llama3.2 --max-creative 3
```

### Managing the persistent config

The config lives at `~/.config/emojo/config.yaml` (editing needs the
`[yaml-config]` extra).

```bash
emojo config path                       # print the file location
emojo config show                       # show effective config (file + env)
emojo config get response_language      # read one value
emojo config set response_language de   # write one value
emojo config set official_languages en,de   # lists: comma-separated
emojo config edit                       # open in $EDITOR
```

Values are validated before they are written, so a typo like
`emojo config set backend bogus` is rejected.

## Python usage

```python
from emojo import suggest

result = suggest("Geschwindigkeit")
for s in result.official:     # list[EmojiSuggestion]
    print(s.emoji, s.reason)
print(result.creative)        # list[EmojiSuggestion]
print(result.from_subset)     # list[EmojiSuggestion]
print(result.model_dump())    # plain dict (pydantic model)
```

### Per-call overrides (these beat the config file)

```python
from emojo import suggest, BackendMode

result = suggest(
    "Recycling",
    subset=["🔄", "♻️", "🔁"],          # category-3 candidates
    backend="ollama",                    # or BackendMode.ollama
    model="llama3.2",
    official_languages=["en", "de"],
    response_language="de",
    max_creative=3,
)
```

### Reusing an explicit config object

```python
from emojo import suggest, EmojoConfig, BackendMode

config = EmojoConfig(
    backend=BackendMode.claude_cli,
    response_language="de",
    official_languages=["en", "de"],
)
result = suggest("fire", config=config)

# Keyword overrides still win over the passed config:
result = suggest("fire", config=config, response_language="en")
```

`EmojoConfig` reads, in order of precedence: keyword overrides on `suggest()`
→ explicit `config=` values → environment variables (`EMOJO_*`) →
`~/.config/emojo/config.yaml` → built-in defaults.

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
