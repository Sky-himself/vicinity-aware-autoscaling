"""Load an optional reference controller from a scenario YAML file."""
from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

import yaml

from .params_base import AutoscalerWrapper, parse_wrapper
from .supported import SUPPORTED_AUTOSCALERS


class AutoscalerLoadError(ValueError):
    """Invalid controller selection or parameters."""


def load_autoscaler_from_yaml(config_path: str | Path) -> Any | None:
    raw = yaml.safe_load(Path(config_path).expanduser().resolve().read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise AutoscalerLoadError("config root must be a mapping")
    return build_from_wrapper(parse_wrapper(raw.get("autoscaler")))


def build_from_wrapper(wrapper: AutoscalerWrapper | None) -> Any | None:
    if wrapper is None or not wrapper.enabled:
        return None
    if wrapper.name not in SUPPORTED_AUTOSCALERS:
        raise AutoscalerLoadError(
            f"unknown autoscaler name '{wrapper.name}'; supported: {SUPPORTED_AUTOSCALERS}"
        )
    module = import_module(f"hierarchical_edge_sim.autoscaler.{wrapper.name}")
    return module.build(wrapper.params, decision_every_k_ticks=wrapper.decision_every_k_ticks)
