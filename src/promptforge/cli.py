"""PromptForge CLI."""
import asyncio

import typer
from rich.console import Console
from rich.panel import Panel

from promptforge import __version__
from promptforge.core.config import EngineConfig
from promptforge.models.schemas import PipelineType

app = typer.Typer(name="promptforge", help="PromptForge - Autonomous AI Development", no_args_is_help=True)
console = Console()


def _get_engine():
    from promptforge.core.engine import PromptForgeEngine
    config = EngineConfig()
    return PromptForgeEngine(config)


@app.command()
def version():
    """Show version."""
    console.print(f"PromptForge v{__version__}")


@app.command()
def run(
    goal: str = typer.Argument(...),
    pipeline: str = typer.Option("full"),
    dry_run: bool = typer.Option(False, "--dry-run"),
):
    """Execute a development pipeline."""
    console.print(Panel(f"[cyan]Goal:[/cyan] {goal}", title="PromptForge"))
    try:
        pipeline_type = PipelineType(pipeline)
    except ValueError:
        console.print(f"[red]Invalid pipeline: {pipeline}[/red]")
        raise typer.Exit(1)
    engine = _get_engine()
    result = asyncio.run(engine.execute_task(goal, pipeline_type, dry_run=dry_run))
    if result.success:
        console.print(Panel(f"[green]Success![/green]\nTokens: {result.total_tokens}", title="Result"))
    else:
        console.print(Panel("[red]Failed[/red]\n" + "\n".join(result.errors), title="Result"))
        raise typer.Exit(1)


@app.command()
def status():
    """Show system status."""
    engine = _get_engine()
    creds = engine.config.validate_credentials()
    console.print(f"NVIDIA: {'OK' if creds['nvidia'] else 'Missing'}")
    console.print(f"GitHub: {'OK' if creds['github'] else 'Missing'}")


if __name__ == "__main__":
    app()