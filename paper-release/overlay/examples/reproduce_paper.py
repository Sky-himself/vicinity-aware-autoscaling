"""Reproduce the four IKT table rows and verify metric/action-log determinism."""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import tempfile

from hierarchical_edge_sim.autoscaler.common.load import load_autoscaler_from_yaml
from hierarchical_edge_sim.env.api import Env

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "hpa-no-floor": (6.81, 9.98, 142.0, 3.81),
    "hpa": (7.45, 11.24, 153.6, 5.37),
    "edge-only": (30.84, 57.80, 702.5, 2.00),
    "edge-cloud": (7.45, 36.78, 521.4, 5.37),
}


def aggregate(run: Path) -> dict[str, float]:
    offered = dropped = missed = weighted_latency = cores = 0.0
    ticks = set()
    for path in sorted(run.rglob("*.log.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                count = float(row["incoming_requests"])
                offered += count
                served = float(row["served_requests"])
                lost = float(row["dropped_requests"])
                if abs(count - served - lost) > 1e-6:
                    raise AssertionError(f"Workload conservation failed in {path}")
                dropped += lost
                missed += float(row["sla_miss_requests"])
                weighted_latency += count * float(row["t_mean_offered_sec"])
                cores += float(row["cpu_core_capacity"])
                ticks.add(int(float(row["time_unit"])))
    if ticks != set(range(1, 722)) or abs(offered - 3_385_510) > 1e-6:
        raise AssertionError(f"Unexpected workload: {len(ticks)} windows, {offered} requests")
    return {
        "drop_percent": 100 * dropped / offered,
        "timeout_percent": 100 * missed / offered,
        "response_ms": 1000 * weighted_latency / offered,
        "average_cores": cores / len(ticks),
    }


def log_checksums(run: Path) -> dict[str, str]:
    paths = [*run.rglob("*.log.csv"), run / "actions.csv"]
    return {p.relative_to(run).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def run_scenario(name: str, output: Path) -> Path:
    config = ROOT / "configs" / "ikt-case-study" / f"{name}.yaml"
    env = Env.from_config(config)
    env.world_spec = replace(env.world_spec, sim=replace(env.world_spec.sim, results_dir=str(output.resolve())))
    return env.run(autoscaler=load_autoscaler_from_yaml(config),
                   now_utc=datetime(2026, 1, 1, tzinfo=UTC))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Compare results with paper and repeat each run")
    args = parser.parse_args()
    results = {}
    with tempfile.TemporaryDirectory(prefix="hierarchical-edge-repeat-") as temporary:
        for name, expected in EXPECTED.items():
            group = "ikt-hierarchy" if name.startswith("edge-") else "ikt-case-study"
            run = run_scenario(name, ROOT / "results" / group / name)
            metrics = aggregate(run)
            checksums = log_checksums(run)
            if args.verify:
                repeated = run_scenario(name, Path(temporary) / name)
                if checksums != log_checksums(repeated):
                    raise AssertionError(f"Non-deterministic metric/action logs: {name}")
                for (key, actual), target, tolerance in zip(metrics.items(), expected, (0.0051, 0.0051, 0.051, 0.0051)):
                    if abs(actual - target) > tolerance:
                        raise AssertionError(f"{name}: {key}={actual:.6f}, paper={target}")
            results[name] = {"metrics": metrics, "log_checksums": checksums,
                             "determinism_verified": args.verify}
            print(f"{name}: drop={metrics['drop_percent']:.2f}% timeout={metrics['timeout_percent']:.2f}% "
                  f"response={metrics['response_ms']:.1f}ms cores={metrics['average_cores']:.2f}")
    report = ROOT / "results" / "paper-reproduction.json"
    report.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {report}")


if __name__ == "__main__":
    main()
