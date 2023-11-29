"""
Token utilities
"""
import json
from datetime import datetime
from http.cookies import SimpleCookie

import jwt
from requests.models import CaseInsensitiveDict

from connman_cli.lib import log
from connman_cli.lib.constants import AppPaths, CIS2Environments


def decode_token_from_headers(headers: CaseInsensitiveDict):
    """Decode Connection Manager access token from the response headers"""
    raw_session_cookie = headers.get("set-cookie")
    session_cookie = SimpleCookie(raw_session_cookie)
    token = session_cookie["__Host-session"].value

    return token, jwt.decode(token, options={"verify_signature": False})


def get_cached_token(env: CIS2Environments, subject: str, silent: bool = False):
    """Get a token from the cache"""
    cached_tokens = []

    for path in AppPaths.cache_dir.glob(f"token-{env.value}-{subject}*.json"):
        timestamp = path.name.removesuffix(".json").split("-").pop()

        if datetime.now() > datetime.fromtimestamp(int(timestamp)):
            path.unlink()
            if not silent:
                log.debug(
                    f"Removed expired token [bold]{path.name}[/bold] from the cache"
                )

            continue

        token = json.loads(path.read_text())
        cached_tokens.append(token)

    if len(cached_tokens) == 0:
        if not silent:
            log.warn("No valid cached tokens are present. Please reauthenticate.")
        return None

    sorted_tokens = sorted(
        cached_tokens, key=lambda token: token["info"]["exp"], reverse=True
    )
    cached_token = sorted_tokens[0]

    if not silent:
        log.info(
            "Access token expires "
            f"[bold]{datetime.fromtimestamp(cached_token['info']['exp'])} UTC[/bold]"
        )

    return cached_token


def cache_token(raw_token: str, token_info: dict, env: CIS2Environments):
    """Cache a new access token"""

    if not AppPaths.cache_dir.exists():
        AppPaths.cache_dir.mkdir(parents=True)

    token_name = f"token-{env.value}-{token_info['sub']}-{token_info['exp']}.json"

    cache_token_path = AppPaths.cache_dir / token_name
    cache_token_path.touch()
    cache_token_path.write_text(json.dumps({"token": raw_token, "info": token_info}))

    log.info(f"Saved temporary access token to [bold]{cache_token_path}[/bold]")
