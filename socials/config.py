"""Configuration and secrets.

Secrets (Buffer/Instagram/Discord tokens) come from the environment. We auto-load a local
`.env` so contributors don't have to export variables by hand — using `find_dotenv()` so the
file is found even when the CLI is run from a subdirectory of the repo. An already-set
environment variable always wins (nothing here overrides the real environment).
"""

import os

from dotenv import find_dotenv, load_dotenv


def load_env() -> None:
    """Load a local `.env` into the environment if one exists (idempotent, non-overriding)."""
    load_dotenv(find_dotenv(usecwd=True), override=False)


def require_env(name: str) -> str:
    """Return the value of a required environment variable, or raise a clear error.

    The message never includes the value — only the variable name and how to set it.
    """
    value = os.environ.get(name)
    if not value:
        raise MissingConfigError(name)
    return value


class MissingConfigError(Exception):
    """A required environment variable is unset. Message tells the user how to fix it."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(
            f"{name} is not set. Copy .env.example to .env and add your {name}, "
            f"or export {name} in your environment."
        )
