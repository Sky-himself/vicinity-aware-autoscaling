# HierarchicalEdgeSim

A discrete-window Python simulator for container autoscaling across edge and
cloud clusters. This repository accompanies **HierarchicalEdgeSim: A
Discrete-Window Simulator for Container Autoscaling at the Edge**, by Ehsan
Moradi and Seyyed Ahmad Javadi, submitted to IKT 2026.

The simulator models finite CPU and memory capacity, per-replica baseline
reservations that do not serve requests, local-preference routing with remote
spillover, overload drops, and analytical M/M/1 latency and SLA scoring.
Controllers resize, spawn, and terminate replicas at window boundaries.

## Install and run

Python 3.12 or newer is required. From the repository root on Linux/WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,plot]'
python examples/run_env_only.py configs/minimal.yaml
python -m pytest -q
```

The minimal example uses the bundled synthetic workload. A run prints its output
directory. No Alibaba download or model checkpoint is required to run the bundled
paper scenarios.

## Reproduce the paper

```bash
python examples/reproduce_paper.py --verify
python examples/plot_ikt_hierarchy.py
```

The first command runs each of the four evaluated scenarios twice, checks
byte-identical metric and action logs, verifies workload conservation, and
compares rounded aggregate metrics with the submitted paper. It writes
`results/paper-reproduction.json`. The second command writes the paper's
edge/cloud allocation figure to `results/ikt-hierarchy/ms588_edge_cloud.pdf`
and a PNG preview alongside it.

The scenario files are in `configs/ikt-case-study/`:

- `hpa-no-floor.yaml`: the table's **No floor** row.
- `hpa.yaml`: the **0.5-core floor** row.
- `edge-only.yaml`: the **Edge only** row.
- `edge-cloud.yaml`: the **Edge and cloud** row and the hierarchy figure.
- `static.yaml` and `vertical.yaml`: additional examples of static provisioning
  and the vertical reference controller.

Run any scenario individually:

```bash
python examples/run_with_autoscaler.py configs/ikt-case-study/edge-cloud.yaml
```

For the additional static/vertical/HPA comparison figure, run `static.yaml`,
`vertical.yaml`, and `hpa.yaml`, then run `python examples/plot_ikt_case_study.py`.

Metric values and action logs are deterministic for identical inputs. Run folder
names include timestamps, and metadata includes local paths; those values are
not expected to be identical across machines. Reproduction is validated on
Python 3.12; cross-version floating-point identity is not asserted.

## Configure an experiment

YAML scenarios declare:

- `sim`: window duration, seed, SLA timeout, routing threshold, and output path.
- `topology`: clusters, workers, CPU/RAM capacities, and inter-cluster delays.
- `apps`: microservices, resource floors/caps, per-request costs, workload CSVs,
  and initial container placements.
- `autoscaler`: optional controller name, decision interval, and parameters.

Workload CSVs contain `time_unit,requests`, with consecutive one-based window
indices. In the paper, each window lasts 60 seconds and `requests` is a count
per window. See `configs/minimal.yaml` for a small complete scenario and the
paper scenarios for multi-cluster configuration. The executable schema and
validation rules are in `src/hierarchical_edge_sim/env/config.py` and
`validate.py`.

Relative trace paths are resolved first against the configuration directory,
then its parent. Relative result paths are resolved against the parent of the
configuration directory. The bundled nested paper configurations account for
this with `../results/...` paths.

## Reference controllers and extension API

The YAML loader exposes three reference controllers:

- `reactive_vertical`: changes existing replica CPU/RAM allocations.
- `kubernetes_hpa`: applies HPA-style replica counts within the home cluster.
- `cloud_spill`: uses the same replica-count formula and places overflow
  replicas in a configured cloud cluster.

Custom controllers can be passed directly to `Env.run`:

```python
from hierarchical_edge_sim.env.api import Env, ResizeAction

class ExampleController:
    name = "example"

    def on_tick_end(self, env: Env, tau: int) -> list:
        # Inspect env.get_container(), env.get_server_free(), and other APIs.
        # Return ResizeAction, SpawnAction, or TerminateAction instances.
        return []

env = Env.from_config("configs/minimal.yaml")
output = env.run(autoscaler=ExampleController())
```

The implemented callback receives the environment and integer tick index.
Controllers can also implement `on_actions_applied(results)` to inspect action
outcomes. The engine orders terminations before resizes and spawns and validates
capacity, floor/cap bounds, ownership, and last-replica constraints. See
`env/api.py` for action fields, inspection methods, and rejection codes.

## Outputs

Each run includes `run_meta.yaml`, `actions.csv`, per-container `*.meta.json`,
and per-container `*.log.csv`. Container logs record allocations, usage,
incoming/served/dropped requests, link delay, mean/P95/P99 response time,
and SLA misses. Retired replicas retain their logs.

The reproduction script computes request-weighted mean latency and drop/timeout
percentages, and averages total allocated cores across all 721 windows.
Generated results are excluded from Git.

## Scope and limitations

The model uses independent decision windows with no cross-window backlog,
fixed link delays, and analytical latency rather than sampled request events.
It does not model mobility, energy, node failures, or microservice RPC graphs.
The baseline controllers are simulation references rather than Kubernetes
integrations.

## Citation and license

Citation metadata is supplied in `CITATION.cff`. The accompanying paper is
submitted; publication details and a DOI will be added when available.

Simulator code is distributed under the [MIT License](LICENSE). The bundled
Alibaba-derived workload has separate provenance described in
[traces/README.md](traces/README.md); the project license does not relicense
third-party data.
