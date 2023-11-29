"""
CIS2 Connection Manager API Client
"""
from json import dumps
from typing import Dict, List, Optional

import requests
import typer

from connman_cli.lib import log
from connman_cli.lib.constants import CIS2Environments, JWKSSigningAlgorithm
from connman_cli.lib.token import get_cached_token


def get_base_api_endpoint(env: CIS2Environments):
    """
    Get the base endpoint for the CIS2 connection manager API
    """
    return (
        f"https://connectionmanager.nhs{env.value}.auth-ptl.cis2.spineservices.nhs.uk"
    )


def check_required_arguments(env: Optional[CIS2Environments], team_id: Optional[str]):
    """Check environment and team ID are set"""

    if not all([env, team_id]):
        log.error("Could not determine an environment or team ID.")
        log.error(
            "Please reauthenticate with a profile, or provide --env and --team-id arguments."
        )
        raise typer.Exit(1)


def _request(
    # pylint:disable=too-many-arguments
    env: CIS2Environments,
    method: str,
    endpoint: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[dict] = None,
    token: Optional[str] = None,
):
    """
    Wraps a request to the CIS2 Connection Manager API
    Adds JWT token in __Host-session cookie if provided
    """
    url = f"{get_base_api_endpoint(env)}{endpoint}"
    log.info(f"Sending request to endpoint=[bold]{endpoint}[/bold]")

    cookies = {}
    if token is not None:
        cookies["__Host-session"] = token

    try:
        response = requests.request(
            method=method,
            url=url,
            timeout=30,
            headers={
                **(headers or {}),
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            cookies=cookies,
            data=dumps(data) if isinstance(data, dict) else data,
        )

    except Exception as exc:
        log.error(
            f"An unexpected error occurred whilst calling the {endpoint} endpoint"
        )
        log.exception()
        raise typer.Exit(1) from exc

    if not response.ok:
        log.warn(f"Received unexpected response from the {endpoint} endpoint")
        log.print_json(
            {
                "Status Code": response.status_code,
                "Request Headers": dict(response.request.headers),
                "Request Body": response.request.body,
                "Headers": dict(response.headers),
                "Response Body": response.text,
            }
        )
        raise typer.Exit(1)

    return response


def ping(env: CIS2Environments):
    """
    Ping the Connection Manager API
    """
    return _request(
        env=env,
        method="GET",
        endpoint="/api/hello_world",
    )


def auth(env: CIS2Environments, secret: str):
    """
    Authenticate with the Connection Manager API using a secret
    """
    headers = {"Authorization": f"SecretAuth {secret}"}
    return _request(env, "POST", "/api/auth", headers)


def list_configs(env: CIS2Environments, team_id: str):
    """
    List configs setup in Connection Manager
    """
    check_required_arguments(env, team_id)

    token = get_cached_token(env, team_id)
    if not token:
        raise typer.Exit(1)

    return _request(
        env=env, method="GET", endpoint=f"/api/configs/{team_id}", token=token["token"]
    )


def get_config(env: CIS2Environments, team_id: str, config_id: str):
    """
    Get a single config from connection manager
    """
    check_required_arguments(env, team_id)

    token = get_cached_token(env, team_id)
    if not token:
        raise typer.Exit(1)

    return _request(
        env=env,
        method="GET",
        endpoint=f"/api/configs/{team_id}/{config_id}",
        token=token["token"],
    )


def create_config(
    # pylint:disable=too-many-arguments
    env: CIS2Environments,
    team_id: str,
    client_name: str,
    description: Optional[str],
    redirect_uri: List[str],
    backchannel_logout_uri: str,
    jwks_uri: str,
    jwks_uri_signing_algorithm: JWKSSigningAlgorithm,
):
    """
    Create a new config in Connection Manager
    """
    check_required_arguments(env, team_id)

    token = get_cached_token(env, team_id)
    if token is None:
        raise typer.Exit(1)

    data = {
        "client_name": client_name,
        "redirect_uris": redirect_uri,
        "backchannel_logout_uri": backchannel_logout_uri,
        "jwks_uri": jwks_uri,
        "jwks_uri_signing_algorithm": jwks_uri_signing_algorithm.value,
    }

    if description is not None:
        data["description"] = description

    return _request(
        env=env,
        token=token["token"],
        method="POST",
        endpoint=f"/api/configs/{team_id}",
        data=data,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )


def update_config(
    env: CIS2Environments,
    team_id: str,
    client_name: str,
    config: dict,
    config_hash: str,
):
    """
    Update a config in Connection Manager
    """
    check_required_arguments(env, team_id)

    token = get_cached_token(env, team_id)
    if token is None:
        raise typer.Exit(1)

    return _request(
        env=env,
        token=token["token"],
        method="PUT",
        endpoint=f"/api/configs/{team_id}/{client_name}?hash={config_hash}",
        data=config,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
