# Two-repository workflow

## Thesis research

`Sky-himself/vicinity-aware-autoscaling` is the original private repository,
renamed without rewriting its history. Develop thesis work on `main`, whose
baseline is `2021f17`. That branch includes the environment and research
controllers in their original `hierarchical_edge_sim` Python namespace.
New documentation and reproduction commits follow the baseline; the source
code was not replaced with the temporary standalone research package.

The local checkout remains `/home/sky/HierarchicalEdgeSim` so existing local
paths do not break. Its `origin` points to the renamed personal repository.
The old private `ikt`, draft branches, and thesis tags are retained.

## IKT simulator release

`ECTLab/HierarchicalEdgeSim` remains the public simulator-only repository.
Its `main` is the independent cleaned release `1633f4b`, tagged `ikt-2026`,
derived from IKT work at `82553f6`. Do not push the raw private `ikt` or thesis
`main` branch to ECTLab: both include thesis history.

The private `public-simulator-release` branch retains the IKT-derived
source, shared-helper refactor, allowlist, public documentation overlays, and
export tool under `paper-release/`. It is a maintenance branch in this same
personal repository, not another GitHub repository. It is deliberately not
merged into thesis `main`.

The public publishing checkout is `/home/sky/HierarchicalEdgeSim-public`.
ECTLab pushes from the thesis checkout remain disabled. Public pushes happen
only from that publishing checkout after export, review, and validation.

To prepare a simulator update, start with a clean private checkout, switch to
`public-simulator-release`, make and commit the intended simulator fix,
and follow that branch's `paper-release/README.md`. Export from a committed
revision that contains the release manifest and IKT scenarios. Then return to
thesis `main`. Transfer shared engine fixes selectively between branches;
do not merge an entire research branch into the public release.

## Consolidated preparation work

The temporary standalone repository was used to prepare the research README,
results figure, and runner. Those useful artifacts have been adapted to the
original layout. The redundant
`Sky-himself/vicinity-aware-autoscaling-preparation` repository was deleted by
the owner. Its local checkout is archived, with pushes disabled. Git bundles and recovery metadata
are stored under
`/home/sky/HierarchicalEdgeSim-backups/2026-11-15/repository-consolidation/`.
