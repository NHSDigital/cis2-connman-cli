"""
Typer CLI Application
"""

import os

import typer
from typing_extensions import Annotated

from connman_cli.commands import auth, config, ping, profile
from connman_cli.lib.config import check_config

app = typer.Typer()

# Add Commands
app.command(name="ping")(ping.command)

# Add Subcommands
app.add_typer(auth.app, name="auth", help="Authentication Subcommands")
app.add_typer(
    config.app, name="config", help="Manage CIS2 Connection Manager Configurations"
)
app.add_typer(profile.app, name="profile", help="View, set and update profiles")


@app.callback()
def main(
    _: typer.Context,
    quiet: Annotated[bool, typer.Option(..., help="Silence log output")] = False,
    colour: Annotated[bool, typer.Option(..., help="Use colours in output")] = True,
):
    """Set Main Command Arguments"""
    os.environ.setdefault("CONNMAN_SILENT", str(quiet))
    os.environ.setdefault("CONNMAN_COLOUR", str(colour))
    check_config()
