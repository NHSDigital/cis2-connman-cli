"""
Config helpers
"""
import configparser

import typer

from connman_cli.lib import api_client, log
from connman_cli.lib.constants import AppPaths, CIS2Environments
from connman_cli.lib.token import decode_token_from_headers


def write_config(config: configparser.ConfigParser):
    """
    Write config to the config path
    """
    AppPaths.config_dir.mkdir(exist_ok=True)
    AppPaths.config_file.touch()

    with open(AppPaths.config_file, "w+", encoding="utf-8") as config_file:
        config.write(config_file)


def check_config():
    """Check if config exists, and initialise it if not"""
    if not AppPaths.config_file.exists():
        init_config()


def init_config():
    """Initialise config prompt"""
    config = configparser.ConfigParser()

    log.info("It looks like this is the first time you have run Connman.")
    log.print("[bold][Credentials][/bold]")
    log.print("Connman can store your secrets for CIS2 Connection Manager as profiles.")
    log.print(
        "You can opt-out of this behaviour if you want to,"
        "however you will have to provide your secret for the relevant environment "
        "each time you need to use Connman.\n"
    )

    if typer.confirm("Would you like to define profiles interactively now?"):
        define_profiles(config)

    return config


def define_profiles(config: configparser.ConfigParser):
    """
    Define profile prompt
    """
    log.print("[bold][Create Profile][/bold]")
    name = typer.prompt("What would you like to name this profile?", type=str).strip()

    profile_key = f"connman.profile.{name}"
    if profile_key in config.sections():
        log.error(f"You already have a profile named {name}.")
        return define_profiles(config)

    env = typer.prompt(
        "Which CIS2 environment do you want to create a profile for? (dev|int|dep)",
        type=CIS2Environments,
    )
    secret = typer.prompt(
        f"Provide your secret for the {env.value} environment", type=str
    ).strip()

    try:
        response = api_client.auth(env, secret)
        _, token_info = decode_token_from_headers(response.headers)
        log.success(
            f"This profile is valid for the following team IDs: {token_info['team_ids']}"
        )
        config[f"connman.profile.{name}"] = {
            "Environment": env.value,
            "Secret": secret,
            "TeamID": token_info["team_ids"][0],
        }

        write_config(config)
        log.success(f"Profile saved to {AppPaths.config_file}")

        if typer.confirm("Would you like to create another profile?"):
            return define_profiles(config)

        return None

    except Exception:  # pylint: disable=broad-exception-caught
        log.error(
            f"Failed to validate the provided secret against the {env.value} environment."
        )
        if typer.confirm("Would you like to try again?"):
            return define_profiles(config)

        return None


def get_config():
    """Get the current config file contents"""
    if not AppPaths.config_file.exists():
        return init_config()

    config = configparser.ConfigParser()
    config.read(AppPaths.config_file)

    return config


def get_current_profile():
    """Get the currently selected profile"""
    config = get_config()

    if config.has_section("connman.profile"):
        active_profile = config["connman.profile"]
        profile = config[active_profile["selected"]]
        profile_name = active_profile["selected"].removeprefix("connman.profile.")

        log.info(f"Using profile [bold]{profile_name}[/bold]")

        env = CIS2Environments(profile["environment"])
        team_id = profile["teamid"]

        return {"env": env, "team_id": team_id}

    return None
