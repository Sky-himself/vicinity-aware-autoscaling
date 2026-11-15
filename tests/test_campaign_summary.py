"""Check quantitative summaries and conservation checks independently of policies."""
import csv
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("campaign", Path(__file__).parents[1] / "experiments/run_campaign.py")
campaign = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(campaign)


def write_log(root, rows):
    path = root / "container.log.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["time_unit", "incoming_requests", "served_requests",
            "dropped_requests", "sla_miss_requests", "t_mean_offered_sec", "cpu_core_capacity"])
        writer.writeheader()
        writer.writerows(rows)


def row(tick=1, offered=10, served=8, dropped=2, missed=3, latency=0.1, cpu=1):
    return dict(zip(["time_unit", "incoming_requests", "served_requests", "dropped_requests",
                     "sla_miss_requests", "t_mean_offered_sec", "cpu_core_capacity"],
                    [tick, offered, served, dropped, missed, latency, cpu]))


def test_weighted_latency_and_allocation_average(tmp_path):
    write_log(tmp_path, [row(), row(tick=2, offered=30, served=30, dropped=0, missed=0, latency=0.3, cpu=3)])
    result = campaign.summarize(tmp_path, 2, 40)
    assert result["drop_percent"] == pytest.approx(5)
    assert result["sla_miss_percent"] == pytest.approx(7.5)
    assert result["mean_response_ms"] == pytest.approx(250)
    assert result["mean_allocated_cores"] == pytest.approx(2)


def test_inconsistent_served_and_dropped_are_rejected(tmp_path):
    write_log(tmp_path, [row(served=5)])
    with pytest.raises(AssertionError, match="conservation"):
        campaign.summarize(tmp_path, 1, 10)


def test_missing_windows_are_rejected(tmp_path):
    write_log(tmp_path, [row()])
    with pytest.raises(AssertionError, match="workload"):
        campaign.summarize(tmp_path, 2, 10)
