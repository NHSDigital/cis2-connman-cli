"""
Auth Commands

Usage: connman auth --help
"""

from datetime import datetime
from time import time
from typing import Optional

import typer
from typing_extensions import Annotated

from connman_cli.lib import log, api_client
from connman_cli.lib.constants import CIS2Environments
from connman_cli.lib.token import cache_token, get_cached_token, decode_token_from_headers
from connman_cli.lib.config import get_config, write_config

app = typer.Typer()


def print_token_info(token_info: dict):
    """Print Access Token Information"""
    data = {
        "Issuer:   ": token_info["iss"],
        "Subject:  ": token_info["sub"],
        "Audience: ": token_info["aud"],
        "Issued At:": f"{datetime.fromtimestamp(token_info['iat'])} UTC",
        "Expires:  ": f"{datetime.fromtimestamp(token_info['exp'])} UTC",
        "Team ID(s)": token_info["team_ids"],
    }

    log.print("\n[bold]--------- Token Info ----------[/bold]")

    for key, value in data.items():
        log.print(f"[cyan bold]{key}[/cyan bold]\t{value}")


@app.command()
def login(
    profile: Annotated[Optional[str], typer.Option()] = None,
    env: Annotated[Optional[CIS2Environments], typer.Option()] = None,
    secret: Annotated[Optional[str], typer.Option()] = None,
):
    """
    Login to a CIS2 Connection Manager Environment

    Usage: connman auth login --profile [PROFILE]

    Usage: connman auth login --env [ENVIRONMENT] --secret [SECRET]
    """
    if not any([profile, env, secret]):
        log.error("Missing --profile or --env and --secret arguments.")
        log.error("Usage: connman auth login --help")
        raise typer.Exit(1)

    if all([profile, env, secret]):
        log.error("Either --profile or --env and --secret arguments are supported.")
        raise typer.Exit(1)

    if profile is not None:
        log.info("Performing Profile Authentication")

        config = get_config()
        profile_key = f"connman.profile.{profile}"

        if not config.has_section(profile_key):
            log.error(f"Profile [bold]{profile}[/bold] does not exist.")
            log.error("Use [bold]connman profile new[/bold] to setup a new profile.")
            raise typer.Exit(1)

        profile_config = config[profile_key]
        log.success(f"Profile [bold]{profile}[/bold] exists.")

        env = CIS2Environments(profile_config["environment"])
        secret = profile_config["secret"]

        response = api_client.auth(env, secret)

        raw_token, token_info = decode_token_from_headers(response.headers)
        print_token_info(token_info)
        cache_token(raw_token, token_info, env)

        config = get_config()
        config["connman.profile"] = {"selected": profile_key, "authtime": int(time())}
        write_config(config)
        log.success(f"Selected Profile: [bold]{profile}[/bold]")

    else:
        log.info("Performing Secret Authentication")

        if not all([env, secret]):
            log.error("Both --env and --secret are required.")
            raise typer.Exit(1)

        response = api_client.auth(env, secret)

        raw_token, token_info = decode_token_from_headers(response.headers)
        print_token_info(token_info)
        cache_token(raw_token, token_info, env)

    log.success("Authenticated with CIS2 Connection Manager")


@app.command()
def status():
    """
    Get the current profile and check for active tokens
    """
    config = get_config()
    if config.has_section("connman.profile"):
        active_profile = config["connman.profile"]
        profile = config[active_profile["selected"]]

        log.print("[bold][Active Profile][/bold]")
        log.print(
            f"Name:\t\t{active_profile['selected'].removeprefix('connman.profile.')}"
        )
        log.print(f"Environment:\t{profile['environment']}")
        log.print(f"Team ID:\t{profile['teamid']}")
        log.print(
            f"Last Auth Time:\t{datetime.fromtimestamp(int(active_profile['authtime']))} UTC"
        )

        token = get_cached_token(
            CIS2Environments(profile["environment"]),
            subject=profile["teamid"],
            silent=True,
        )

        log.print(f"Token Active:\t{bool(token)}")
