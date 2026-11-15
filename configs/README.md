# Scenario configurations

Run configurations with `python examples/run_with_autoscaler.py CONFIG.yaml`.
The integrated loader selects research controllers and reference controllers;
all use the simulator snapshot included in this repository.

Numbered files preserve existing experiment identifiers. Early files exercise
synthetic mechanics; later files define the Alibaba evaluations. The current
research campaign runner groups 33–37 (two services), 38–42 (four services),
43–47 (eight services), and 50–54 (split ownership). Configs 48–49 are target
utilization variants of the two-service scenario.

See `docs/EXPERIMENTS.md` for reproduction and metric definitions. These configs
belong to the thesis research; the IKT-only scenarios remain with the simulator.
