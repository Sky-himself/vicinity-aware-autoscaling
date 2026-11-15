"""Run a research comparison and save aggregate metrics and input provenance."""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import time

import subprocess
from hierarchical_edge_sim.env.api import Env
from hierarchical_edge_sim.env.config import resolve_traces_dir
from hierarchical_edge_sim.env.metrics_log import make_run_id
from hierarchical_edge_sim.autoscaler.common.load import load_autoscaler_from_yaml

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_BASE_COMMIT = "2021f17f0346153f7df31680d2fc92d75597b5fa"
CAMPAIGNS = {
    "two-ms": {"reactive": 33, "persistence": 34, "hpa": 35, "proscale": 36, "tcn": 37},
    "four-ms": {"reactive": 38, "persistence": 39, "tcn": 40, "hpa": 41, "proscale": 42},
    "eight-ms": {"reactive": 43, "persistence": 44, "hpa": 45, "proscale": 46, "tcn": 47},
    "split-owner": {"reactive": 50, "persistence": 51, "hpa": 52, "proscale": 53, "tcn": 54},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(run: Path, horizon: int, expected_requests: float) -> dict[str, float]:
    incoming = dropped = missed = latency = cores = 0.0
    ticks = set()
    for log in sorted(run.rglob("*.log.csv")):
        with log.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                offered = float(row["incoming_requests"])
                lost = float(row["dropped_requests"])
                served = float(row["served_requests"])
                if abs(offered - served - lost) > 1e-6:
                    raise AssertionError(f"Request conservation failed: {log}")
                incoming += offered
                dropped += lost
                missed += float(row["sla_miss_requests"])
                latency += offered * float(row["t_mean_offered_sec"])
                cores += float(row["cpu_core_capacity"])
                ticks.add(int(float(row["time_unit"])))
    if ticks != set(range(1, horizon + 1)) or abs(incoming - expected_requests) > 1e-5:
        raise AssertionError(f"Logged workload does not match input: {incoming} != {expected_requests}")
    return {"incoming_requests": incoming, "dropped_requests": dropped,
            "drop_percent": 100 * dropped / incoming,
            "sla_miss_percent": 100 * missed / incoming,
            "mean_response_ms": 1000 * latency / incoming,
            "mean_allocated_cores": cores / horizon}


def plot_comparison(rows: list[dict], output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = {"hpa": "Home HPA", "reactive": "Reactive", "proscale": "ProScale-style",
              "persistence": "Persistence", "tcn": "TCN"}
    order = ["hpa", "reactive", "proscale", "persistence", "tcn"]
    rows = sorted(rows, key=lambda row: order.index(row["policy"]))
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), layout="constrained")
    for ax, metric, title in zip(axes,
            ("drop_percent", "sla_miss_percent", "mean_allocated_cores"),
            ("Dropped requests (%)", "SLA misses (%)", "Mean allocated CPU (cores)")):
        bars = ax.bar([labels[row["policy"]] for row in rows], [row[metric] for row in rows],
                      color=["#8596a5" if row["policy"] != "tcn" else "#147d92" for row in rows])
        ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=9)
        ax.set_title(title, fontsize=11)
        ax.tick_params(axis="x", labelrotation=35, labelsize=9)
        ax.set_ylim(0, max(row[metric] for row in rows) * 1.22)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Two-service shared-owner replay | 721 one-minute windows | seed 42", fontsize=12)
    if any(row["policy"] == "tcn" for row in rows):
        fig.supxlabel("TCN fitted on the replay interval; compare resource allocation alongside QoS.", fontsize=9)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", choices=CAMPAIGNS, default="two-ms")
    parser.add_argument("--include-tcn", action="store_true")
    args = parser.parse_args()
    if args.include_tcn:
        try:
            import torch
            torch.set_num_threads(1)
        except ImportError as error:
            raise SystemExit("Install the tcn extra before using --include-tcn") from error
    output = ROOT / "results" / args.campaign
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    provenance = {"research_baseline_commit": RESEARCH_BASE_COMMIT,
                  "code_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(), "python": platform.python_version(),
                  "campaign": args.campaign, "created_utc": datetime.now(UTC).isoformat(),
                  "tcn_evaluation": "same-trace fit/replay; not held-out", "runs": {}, "packages": {}}
    provenance["research_source_sha256"] = {
        path.relative_to(ROOT).as_posix(): sha256(path)
        for path in sorted([*ROOT.glob("src/**/*.py"), Path(__file__).resolve()])}
    for package in ("hierarchical-edge-sim", "pyyaml", "matplotlib", "torch"):
        try:
            provenance["packages"][package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            pass
    rows = []
    for label, number in CAMPAIGNS[args.campaign].items():
        if label == "tcn" and not args.include_tcn:
            continue
        [config] = list((ROOT / "configs").glob(f"{number:02d}-*.yaml"))
        env = Env.from_config(config)
        horizon = env.traces.horizon
        expected = sum(env.traces.get(ms, tick) for ms in env.list_microservices() for tick in range(1, horizon + 1))
        result_base = output / label
        now = datetime.now(UTC)
        while (result_base / make_run_id(env.world_spec.sim.seed, now)).exists():
            now += timedelta(seconds=1)
        env.world_spec = replace(env.world_spec, sim=replace(env.world_spec.sim, results_dir=str(result_base)))
        run = env.run(autoscaler=load_autoscaler_from_yaml(config), now_utc=now)
        row = {"policy": label, **summarize(run, horizon, expected)}
        rows.append(row)
        trace_dir = resolve_traces_dir(env.world_spec.traces_dir, env.world_spec.source_path)
        inputs = [config, *[trace_dir / ms.trace_file for app in env.world_spec.apps for ms in app.microservices]]
        if label == "tcn":
            import yaml
            params = yaml.safe_load(config.read_text())["autoscaler"]["params"]
            model_dirs = list((params.get("model_dirs") or {}).values())
            if not model_dirs:
                model_dirs = [params.get("model_dir", "models/tcn_delta_ms588_v2")]
            inputs.extend(path for directory in model_dirs for path in sorted((ROOT / directory).glob("*")) if path.is_file())
        provenance["runs"][label] = {"directory": run.relative_to(ROOT).as_posix(), "horizon": horizon,
            "seed": env.world_spec.sim.seed, "inputs_sha256": {p.relative_to(ROOT).as_posix(): sha256(p) for p in inputs},
            "logs_sha256": {p.relative_to(run).as_posix(): sha256(p) for p in sorted(run.rglob("*.log.csv"))}}
        print(f"{label}: drop={row['drop_percent']:.2f}% SLA={row['sla_miss_percent']:.2f}% cores={row['mean_allocated_cores']:.2f}")
    with (output / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    provenance["elapsed_seconds"] = time.perf_counter() - started
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    # The overview figure intentionally describes only the reference two-MS group.
    if args.campaign == "two-ms":
        plot_comparison(rows, output / "comparison.png")
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
