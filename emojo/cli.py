from __future__ import annotations

import sys
import threading
from contextlib import contextmanager
from typing import Annotated, Iterator, Optional

import grapheme
import typer
from typer.core import TyperGroup

from .config import BackendMode, EmojoConfig, config_path
from .models import EmojiResult
from .suggest import suggest


class _DefaultGroup(TyperGroup):
    """Treat a bare first argument (e.g. ``emojo "Feuer"``) as the ``suggest`` command."""

    default_command = "suggest"

    def parse_args(self, ctx, args):  # type: ignore[override]
        if args and args[0] not in self.commands and not args[0].startswith("-"):
            args = [self.default_command, *args]
        return super().parse_args(ctx, args)


app = typer.Typer(
    cls=_DefaultGroup,
    help="Suggest emojis for any topic. Run a topic directly, e.g. `emojo \"Feuer\"`.",
    no_args_is_help=True,
    add_completion=True,
)
config_app = typer.Typer(help="Show and edit the persistent config file.")
app.add_typer(config_app, name="config")

# A space wandering through five dots.
_SPINNER_FRAMES = [" ....", ". ...", ".. ..", "... .", ".... "]


@contextmanager
def _progress(label: str, enabled: bool) -> Iterator[None]:
    """Show an animated wandering-dot indicator on stderr while the block runs."""
    if not enabled:
        yield
        return

    stop = threading.Event()

    def spin() -> None:
        i = 0
        while not stop.is_set():
            frame = _SPINNER_FRAMES[i % len(_SPINNER_FRAMES)]
            sys.stderr.write(f"\r{label} {frame}")
            sys.stderr.flush()
            i += 1
            stop.wait(0.15)
        sys.stderr.write("\r" + " " * (len(label) + 7) + "\r")
        sys.stderr.flush()

    thread = threading.Thread(target=spin, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join()


def _render(result: EmojiResult) -> None:
    typer.echo(f"\nEmoji suggestions for: {result.topic}\n")

    sections = [
        ("1. Official matches (Unicode name/keywords):", result.official, "(none found)"),
        ("2. Creatively used (common but unofficial):", result.creative, "(none)"),
        ("3. Best from subset:", result.from_subset, "(none)"),
    ]
    for title, items, empty in sections:
        typer.echo(title)
        if items:
            for s in items:
                typer.echo(f"   {s.emoji}  — {s.reason}")
        else:
            typer.echo(f"   {empty}")
        typer.echo("")


def suggest_cmd(
    topic: Annotated[str, typer.Argument(help="Topic, keyword, or symbol to find emojis for")],
    subset: Annotated[
        Optional[str],
        typer.Option("--subset", "-s", help="Custom emoji subset as a single string"),
    ] = None,
    backend: Annotated[
        Optional[BackendMode],
        typer.Option("--backend", "-b", help="Backend: claude-cli (default), anthropic, ollama"),
    ] = None,
    model: Annotated[
        Optional[str],
        typer.Option("--model", "-m", help="Model override (backend-specific model name)"),
    ] = None,
    official_languages: Annotated[
        Optional[str],
        typer.Option(
            "--languages", "-l",
            help="Comma-separated languages for official search, e.g. 'en,de'",
        ),
    ] = None,
    response_language: Annotated[
        Optional[str],
        typer.Option("--response-language", "-r", help="Language for the reason texts, e.g. 'de'"),
    ] = None,
    max_official: Annotated[Optional[int], typer.Option(help="Max official matches")] = None,
    max_creative: Annotated[Optional[int], typer.Option(help="Max creative matches")] = None,
    max_subset: Annotated[Optional[int], typer.Option(help="Max subset matches")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    """Suggest emojis for TOPIC. CLI options override the config file."""
    langs = [s.strip() for s in official_languages.split(",")] if official_languages else None
    active_subset = list(grapheme.graphemes(subset)) if subset else None

    animate = not json_output and sys.stderr.isatty()
    try:
        with _progress("Searching", animate):
            result = suggest(
                topic,
                subset=active_subset,
                backend=backend,
                model=model,
                official_languages=langs,
                response_language=response_language,
                max_official=max_official,
                max_creative=max_creative,
                max_subset=max_subset,
            )
    except (RuntimeError, OSError, ValueError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(result.model_dump_json(indent=2))
    else:
        _render(result)


# Register under the name `suggest` (function name avoids shadowing the import).
app.command(name="suggest")(suggest_cmd)


# --------------------------------------------------------------------------- #
# config subcommands
# --------------------------------------------------------------------------- #

_LIST_FIELDS = {"official_languages", "default_subset"}
_INT_FIELDS = {"max_official", "max_creative", "max_subset"}


def _require_yaml() -> "object":
    try:
        import yaml
    except ImportError:
        typer.secho(
            "Editing the config file needs PyYAML. Install with:\n"
            "    pip install \"emojo[yaml-config]\"",
            fg=typer.colors.RED, err=True,
        )
        raise typer.Exit(code=1)
    return yaml


def _coerce(key: str, raw: str) -> object:
    if key in _LIST_FIELDS:
        return [s.strip() for s in raw.split(",") if s.strip()]
    if key in _INT_FIELDS:
        try:
            return int(raw)
        except ValueError:
            typer.secho(f"'{key}' expects an integer, got: {raw!r}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
    return raw


@config_app.command("path")
def config_path_cmd() -> None:
    """Print the config file path."""
    typer.echo(str(config_path()))


@config_app.command("show")
def config_show_cmd() -> None:
    """Show the effective config (file + environment merged)."""
    yaml = _require_yaml()
    data = EmojoConfig().model_dump(mode="json")
    typer.echo(yaml.safe_dump(data, allow_unicode=True, sort_keys=True).rstrip())


@config_app.command("get")
def config_get_cmd(
    key: Annotated[str, typer.Argument(help="Config key to read")],
) -> None:
    """Print the effective value of a single config KEY."""
    if key not in EmojoConfig.model_fields:
        typer.secho(f"Unknown config key: {key}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.echo(getattr(EmojoConfig(), key))


@config_app.command("set")
def config_set_cmd(
    key: Annotated[str, typer.Argument(help="Config key")],
    value: Annotated[str, typer.Argument(help="New value (comma-separated for lists)")],
) -> None:
    """Persist KEY=VALUE to the config file."""
    if key not in EmojoConfig.model_fields:
        valid = ", ".join(sorted(EmojoConfig.model_fields))
        typer.secho(f"Unknown config key: {key}\nValid keys: {valid}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    yaml = _require_yaml()
    coerced = _coerce(key, value)

    path = config_path()
    data: dict = {}
    if path.exists():
        data = yaml.safe_load(path.read_text()) or {}

    candidate = {**data, key: coerced}
    try:
        EmojoConfig.model_validate(candidate)  # validate before writing
    except Exception as exc:  # noqa: BLE001
        typer.secho(f"Invalid value for '{key}': {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(candidate, allow_unicode=True, sort_keys=True))
    typer.secho(f"Set {key} = {coerced}  ({path})", fg=typer.colors.GREEN)


@config_app.command("edit")
def config_edit_cmd() -> None:
    """Open the config file in $EDITOR (creates it if missing)."""
    path = config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# emojo config\n")
    typer.launch(str(path))


def run() -> None:
    app()
