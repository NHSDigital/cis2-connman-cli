"""
Logging utils
"""
import os
from typing import Any

from rich.console import Console

console = Console()


def print(text, force: bool = False):  # pylint: disable=redefined-builtin
    """Basic console print"""
    highlight = os.getenv("CONNMAN_COLOUR") == "True"
    if os.getenv("CONNMAN_SILENT", "False") != "True" or force:
        console.print(text, highlight=highlight, markup=highlight)


def debug(text: str) -> None:
    "Debug log"
    print(f"[bright_black][bold]DEBUG[/bold]\t {text}[/bright_black]")


def success(text: str) -> None:
    """Success log"""
    print(f"[green][bold]SUCCESS[/bold]\t {text}[/green]")


def info(text: str) -> None:
    """Info log"""
    print(f"[blue][bold]INFO[/bold]\t {text}[/blue]")


def warn(text: str) -> None:
    """Warn log"""
    print(f"[yellow][bold]WARNING[/bold]\t {text}[/yellow]")


def error(text: str) -> None:
    """Error log"""
    print(f"[red][bold]ERROR[/bold]\t {text}[/red]")


def exception(force: bool = False):
    """Print an exception"""
    if os.getenv("CONNMAN_SILENT", "0") != "1" or force:
        console.print_exception()


def print_json(entries: Any, force: bool = False):
    """Print JSON output"""
    if os.getenv("CONNMAN_SILENT", "0") != "1" or force:
        console.print_json(
            data=entries, highlight=os.getenv("CONNMAN_COLOUR") == "True"
        )
