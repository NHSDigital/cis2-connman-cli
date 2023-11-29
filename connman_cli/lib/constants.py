"""
Constants
"""
# pylint:disable=too-few-public-methods


from enum import Enum
from pathlib import Path


class AppPaths:
    """
    Application Paths
    """

    config_dir = Path("~/.config/connman-cli").expanduser()
    config_file = Path("~/.config/connman-cli/config.ini").expanduser()
    cache_dir = Path("~/.cache/connman-cli").expanduser()


class CIS2Environments(str, Enum):
    """
    CIS2 Connection Manager Environments
    """

    # pylint: disable=invalid-name

    dev = "dev"
    int = "int"
    dep = "dep"


class JWKSSigningAlgorithm(str, Enum):
    """
    JWKS Signing Algorithms
    """

    RS256 = "RS256"
    RS512 = "RS512"
