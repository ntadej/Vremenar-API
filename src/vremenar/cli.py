"""Simple development CLI."""

from argparse import ArgumentParser

import uvicorn


def main() -> None:
    """Run simple development CLI."""
    parser = ArgumentParser(
        prog="Vremenar",
        description="Simple development CLI for Vremenar API.",
    )
    args = parser.parse_args()  # noqa: F841

    # uvicorn vremenar.main:app --reload --reload-dir src/vremenar --log-level debug
    uvicorn.run(
        "vremenar.main:app",
        reload=True,
        reload_dirs=["src/vremenar"],
        log_level="debug",
    )
