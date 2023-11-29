"""
Main application entrypoint
"""

from connman_cli.app import app
from connman_cli.lib.config import check_config


def main():
    """Entrypoint"""
    check_config()
    app()
