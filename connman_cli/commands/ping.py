"""
Ping command

Usage: connman ping --help
"""

import typer
from typing_extensions import Annotated

from connman_cli.lib import api_client
from connman_cli.lib.constants import CIS2Environments


def command(
    env: Annotated[CIS2Environments, typer.Option(prompt=True, show_choices=True)]
):
    """Pings the /hello_world endpoint of the CIS2 Connection Manager API"""
    api_client.ping(env)
