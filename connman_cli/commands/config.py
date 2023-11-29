"""
Config Commands

Usage: connman config --help
"""
from typing import List, Optional

import typer
from typing_extensions import Annotated

from connman_cli.lib import api_client, log
from connman_cli.lib.config import get_current_profile
from connman_cli.lib.constants import CIS2Environments, JWKSSigningAlgorithm

app = typer.Typer()


@app.command(name="get")
def get_single_config(
    config_id: Annotated[str, typer.Argument()],
    env: Annotated[Optional[CIS2Environments], typer.Option()] = None,
    team_id: Annotated[Optional[str], typer.Option()] = None,
):
    """
    Get a single config by config name
    """
    profile = get_current_profile()
    if profile:
        env = profile["env"]
        team_id = profile["team_id"]

    response = api_client.get_config(env, team_id, config_id)
    config = response.json()
    log.print_json(config, force=True)


@app.command(name="list")
def list_all_configs(
    env: Annotated[Optional[CIS2Environments], typer.Option()] = None,
    team_id: Annotated[Optional[str], typer.Option()] = None,
    with_detail: bool = False,
):
    """
    List all configs within a single environment and team
    """
    profile = get_current_profile()
    if profile:
        env = profile["env"]
        team_id = profile["team_id"]

    response = api_client.list_configs(env, team_id)

    data = response.json()
    config_list = data.get("configs", [])

    if len(config_list) == 0:
        log.warn("You have not set up any configs for this team.")
        raise typer.Exit(0)

    log.success(f"Retrieved {len(config_list)} config entries")

    if not with_detail:
        log.debug(
            "Listing all config entries. Use --with-detail for more information about each entry."
        )
        log.print_json(config_list, force=True)
        raise typer.Exit(0)

    configs = {
        config_id: api_client.get_config(env, team_id, config_id).json()
        for config_id in config_list
    }

    log.print_json(configs, force=True)


@app.command()
def create(
    # pylint:disable=too-many-arguments
    client_name: Annotated[
        str, typer.Argument(..., help="The name of the client to be created")
    ],
    redirect_uri: Annotated[
        List[str], typer.Option(..., help="The redirect URI of the client")
    ],
    backchannel_logout_uri: Annotated[
        str, typer.Option(..., help="The backchannel logout URI of the client")
    ],
    jwks_uri: Annotated[
        str, typer.Option(..., help="The JSON Web Key URI of the client")
    ],
    jwks_uri_signing_algorithm: Annotated[
        JWKSSigningAlgorithm,
        typer.Option(..., help="The algorithm used for the JSON Web Key"),
    ],
    description: Annotated[
        Optional[str], typer.Option(..., help="Description of the client")
    ] = None,
    env: Annotated[
        CIS2Environments, typer.Option(..., help="CIS2 Connection Manager Environment")
    ] = None,
    team_id: Annotated[str, typer.Option(..., help="Team ID to use")] = None,
):
    """
    Create a new config
    """
    profile = get_current_profile()
    if profile:
        env = profile["env"]
        team_id = profile["team_id"]

    response = api_client.create_config(
        env,
        team_id,
        client_name,
        description,
        redirect_uri,
        backchannel_logout_uri,
        jwks_uri,
        jwks_uri_signing_algorithm,
    )
    if not response.ok:
        raise typer.Exit(1)

    config = response.json()

    log.success(f"Created config with name=[bold]{config['config_name']}[/bold]")
    log.print_json(config, force=True)


@app.command()
def edit(
    # pylint:disable=too-many-arguments
    client_name: Annotated[
        str, typer.Argument(..., help="The name of the client to be modified")
    ],
    redirect_uri: Annotated[
        Optional[List[str]],
        typer.Option(..., help="The new redirect URI of the client"),
    ] = None,
    backchannel_logout_uri: Annotated[
        Optional[str],
        typer.Option(..., help="The new backchannel logout URI of the client"),
    ] = None,
    jwks_uri: Annotated[
        str, typer.Option(..., help="The new JSON Web Key URI of the client")
    ] = None,
    jwks_uri_signing_algorithm: Annotated[
        JWKSSigningAlgorithm,
        typer.Option(..., help="The new algorithm used for the JSON Web Key"),
    ] = None,
    description: Annotated[
        Optional[str], typer.Option(..., help="Description of the client")
    ] = None,
    env: Annotated[
        CIS2Environments,
        typer.Option(
            ...,
            help="CIS2 Connection Manager Environment (not required if using profiles)",
        ),
    ] = None,
    team_id: Annotated[
        str, typer.Option(..., help="Team ID to use (not required if using profiles)")
    ] = None,
):
    """
    Edit an existing config
    """
    if not any(
        [
            redirect_uri,
            backchannel_logout_uri,
            jwks_uri,
            jwks_uri_signing_algorithm,
            description,
        ]
    ):
        log.error("No arguments were provided.")
        raise typer.Exit(1)

    profile = get_current_profile()
    if profile:
        env = profile["env"]
        team_id = profile["team_id"]

    response = api_client.get_config(env, team_id, client_name)
    data = response.json()

    client = data["client_config"]

    new_client = {
        **client,
        "redirect_uris": redirect_uri or client["redirect_uris"],
        "backchannel_logout_uri": backchannel_logout_uri
        or client["backchannel_logout_uri"],
        "jwks_uri": jwks_uri or client["jwks_uri"],
        "jwks_uri_signing_algorithm": jwks_uri_signing_algorithm.value
        if jwks_uri_signing_algorithm
        else client["jwks_uri_signing_algorithm"],
    }

    if description:
        new_client["description"] = description

    if new_client == client:
        log.warn("The new client is identical to the current client.")

    log.info(f"Saving modified client with hash=[bold]{data['hash']}[/bold]")

    response = api_client.update_config(
        env, team_id, client_name, new_client, data["hash"]
    )

    log.success(f"Updated client [bold]{client_name}[/bold]")
    log.print_json(new_client, force=True)
