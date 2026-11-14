"""Validate all distributed scenarios and the public controller registry."""
from pathlib import Path

import pytest

from hierarchical_edge_sim.autoscaler.common.load import load_autoscaler_from_yaml
from hierarchical_edge_sim.autoscaler.common.supported import SUPPORTED_AUTOSCALERS
from hierarchical_edge_sim.env.api import Env


@pytest.mark.parametrize("scenario", ["static", "vertical", "hpa", "hpa-no-floor", "edge-only", "edge-cloud"])
def test_paper_scenario_loads(project_root: Path, scenario: str):
    path = project_root / "configs" / "ikt-case-study" / f"{scenario}.yaml"
    env = Env.from_config(path)
    scaler = load_autoscaler_from_yaml(path)
    assert env.list_microservices() == ["ms588"]
    assert (scaler is None) == (scenario == "static")


def test_reference_controller_names():
    assert SUPPORTED_AUTOSCALERS == ["reactive_vertical", "kubernetes_hpa", "cloud_spill"]
