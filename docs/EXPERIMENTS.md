# Experiment guide

The research method and evaluation artifact use the integrated simulator
snapshot in this repository. The research baseline is `2021f17`; the runner
records the current Git revision and SHA-256 hashes of the engine, controller,
scenario, trace, and model files. Engine changes should be explicit and
followed by baseline reruns. No separate simulator installation is required.

## Campaigns

- `two-ms`: configs 33–37, shared owner, two services, 48 CPU cores total.
- `split-owner`: configs 50–54, two distinct home clusters and a shared spare
  cluster, two services, 48 CPU cores total.
- `four-ms`: configs 38–42, four services, a shared home and neighboring cluster.
- `eight-ms`: configs 43–47, eight services, 80 CPU cores total.

Each group compares the reactive policy, persistence front-end, home HPA,
reduced ProScale-style baseline, and optional TCN front-end. Read the individual
YAML files for resource budgets, route thresholds, forecast horizons, decision
intervals, seeds, and controller parameters. Configs 48–49 change the target
utilization for the two-service persistence/TCN policies.

## Run and inspect

```bash
python experiments/run_campaign.py --campaign two-ms --include-tcn
```

The campaign runner imports this repository's loader and passes the selected
controller to its integrated environment's `Env.run`. Independent run directories are
retained, and the campaign's summary/provenance files describe the latest run.

Individual YAML runs remain available:

```bash
python examples/run_with_autoscaler.py configs/33-demo_alibaba_2ms_vicinity_reactive.yaml
python examples/compare_trace_vs_log.py RESULTS_RUN_DIRECTORY
python examples/compare_reactive_baseline.py --run reactive REACTIVE_RUN --run persistence PERSISTENCE_RUN
```

Generated raw results are ignored by Git. Compact recorded references live
under `results/reference/`; the initial two-service reference includes actual
rerun measurements and checksums rather than copied historical headline values.
The reference plot is under `figures/`.

## Metrics and validation

- Drop percentage: dropped requests divided by offered requests across all
  services and all windows.
- SLA-miss percentage: logged deadline violations divided by offered requests.
- Mean response time: offered-request-weighted `t_mean_offered_sec`, in ms.
- Mean allocated CPU: total per-replica CPU allocations summed across workers,
  divided by the number of windows. This is allocation, not CPU usage.

The runner checks per-record offered = served + dropped and that total logged
offers match the sum of the configured input traces. Each series has 721
one-minute windows. Main summary values include cold start; per-run analysis
can additionally show the period after the 60-window predictor lookback.

## Interpretation and outstanding work

TCN weights were fitted on the same trace interval used for these replay
experiments. They must not be described as held-out evaluation. A separate
training/test protocol and complete training pipeline are needed before making
generalization claims. The reduced ProScale baseline and home-only HPA have
different operational constraints from the proposed sharing policy; describe
those constraints alongside comparisons. Full seeds/ablations and final
paper-figure mappings will follow the thesis evaluation protocol.
