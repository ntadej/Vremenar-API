"""Simple development CLI."""

from __future__ import annotations

from argparse import ArgumentParser

import uvicorn


def main() -> None:
    """Run simple development CLI."""
    parser = ArgumentParser(
        prog="Vremenar",
        description="Simple development CLI for Vremenar API.",
    )
    parser.parse_args()

    # uvicorn vremenar.main:app --reload --reload-dir src/vremenar --log-level debug
    uvicorn.run(
        "vremenar.main:app",
        reload=True,
        reload_dirs=["src/vremenar"],
        log_level="debug",
    )
