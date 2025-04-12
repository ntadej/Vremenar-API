"""Vremenar models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from pydantic import ConfigDict, JsonValue


def get_examples(config: ConfigDict) -> list[JsonValue]:
    """Get examples from model config."""
    if not isinstance(config["json_schema_extra"], dict):  # pragma: no cover
        return []

    json_schema_extra: dict[str, list[JsonValue]] = cast(
        "dict[str, list[JsonValue]]",
        config["json_schema_extra"],
    )

    return json_schema_extra["examples"]


def extend_examples(
    config: ConfigDict,
    example: dict[str, Any],
) -> JsonValue:
    """Get and extend examples from model config."""
    return [cast("dict[str, Any]", e) | example for e in get_examples(config)]
