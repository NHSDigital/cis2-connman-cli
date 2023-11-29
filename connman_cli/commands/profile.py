"""
Profile commands

Usage: connman profile --help
"""

import typer
from typing_extensions import Annotated

from connman_cli.lib import log
from connman_cli.lib.config import define_profiles, get_config

app = typer.Typer()


@app.command(name="new")
def new_profile():
    """Create a new profile"""
    config = get_config()
    define_profiles(config)


@app.command(name="list")
def list_profiles():
    """List setup profiles"""
    config = get_config()
    profiles = [
        section.replace("connman.profile.", "")
        for section in config.sections()
        if "connman.profile." in section
    ]

    log.print_json(profiles, force=True)


@app.command(name="get")
def get_profile(profile_name: Annotated[str, typer.Argument()]):
    """
    Get profile details
    """
    config = get_config()
    profile_key = f"connman.profile.{profile_name}"

    if profile_key not in config.sections():
        log.error(f"Profile [bold]{profile_name}[/bold] not found.")
        raise typer.Exit(1)

    log.print_json(dict(config[profile_key].items()), force=True)
