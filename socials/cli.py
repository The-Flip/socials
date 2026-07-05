"""Command-line entry point for socials.

The CLI is the first surface (reports run from a terminal); Discord delivery and a
web interface come later. See docs/plans/Product.md for the "why".
"""

import click


@click.group()
@click.version_option()
def cli() -> None:
    """Reporting, alerts, and assistance for The Flip's social media volunteers."""


@cli.command()
def report() -> None:
    """Run a social-media report.

    Placeholder: no platforms are connected yet. Instagram is the first planned
    integration — see docs/plans/Product.md.
    """
    raise click.ClickException(
        "No reports are implemented yet. Instagram reporting is the first planned "
        "feature — see docs/plans/Product.md."
    )
