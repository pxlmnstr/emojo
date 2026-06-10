from __future__ import annotations

from typing import Annotated, Optional

import grapheme
import typer

from .config import BackendMode, EmojoConfig
from .suggest import suggest

app = typer.Typer(help="Suggest emojis for any topic.")


@app.command()
def main(
    topic: Annotated[str, typer.Argument(help="Topic, keyword, or symbol to find emojis for")],
    subset: Annotated[
        Optional[str],
        typer.Option("--subset", "-s", help="Custom emoji subset as a single string"),
    ] = None,
    model: Annotated[
        Optional[str],
        typer.Option("--model", "-m", help="Model override (backend-specific model name)"),
    ] = None,
    backend: Annotated[
        Optional[BackendMode],
        typer.Option(
            "--backend", "-b",
            help="Backend: claude-cli (default), anthropic, or ollama",
        ),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Output raw JSON"),
    ] = False,
) -> None:
    config = EmojoConfig()
    if backend:
        config.backend = backend
    if model:
        if config.backend == BackendMode.claude_cli:
            config.claude_cli_model = model
        elif config.backend == BackendMode.ollama:
            config.ollama_model = model
        else:
            config.model = model

    active_subset = list(grapheme.graphemes(subset)) if subset else None

    try:
        result = suggest(topic, subset=active_subset, config=config)
    except RuntimeError as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(result.model_dump_json(indent=2))
        return

    typer.echo(f"\nEmoji suggestions for: {result.topic}\n")

    typer.echo("1. Official matches (Unicode name/description):")
    if result.official:
        for s in result.official:
            typer.echo(f"   {s.emoji}  — {s.reason}")
    else:
        typer.echo("   (none found)")

    typer.echo("\n2. Creatively used (common but unofficial):")
    if result.creative:
        for s in result.creative:
            typer.echo(f"   {s.emoji}  — {s.reason}")
    else:
        typer.echo("   (none)")

    typer.echo("\n3. Best from subset:")
    if result.from_subset:
        for s in result.from_subset:
            typer.echo(f"   {s.emoji}  — {s.reason}")
    else:
        typer.echo("   (none)")

    typer.echo("")


def run() -> None:
    app()
