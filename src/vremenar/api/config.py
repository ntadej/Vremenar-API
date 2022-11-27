"""Common API configuration."""

from typing import Any

defaults: dict[str, Any] = {}
defaults.setdefault("response_model_exclude_unset", True)
defaults.setdefault("response_model_exclude_none", True)
