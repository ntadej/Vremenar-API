"""Vremenar models."""
from typing import Any, cast

from pydantic import ConfigDict


def get_examples(config: ConfigDict) -> list[dict[str, Any]]:
    """Get examples from model config."""
    if not isinstance(config["json_schema_extra"], dict):
        return []

    json_schema_extra: dict[str, list[dict[str, Any]]] = cast(
        dict[str, list[dict[str, Any]]],
        config["json_schema_extra"],
    )

    return json_schema_extra["examples"]


def extend_examples(
    config: ConfigDict,
    example: dict[str, Any],
) -> list[dict[str, Any]]:
    """Get and extend examples from model config."""
    return [e | example for e in get_examples(config)]
