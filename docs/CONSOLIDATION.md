# Repository consolidation — 15 November 2026

## Preserved repository identity and history

The original private `Sky-himself/HierarchicalEdgeSim` repository (GitHub ID
1390709238) was renamed to `Sky-himself/vicinity-aware-autoscaling`.
Its original branch and tag history is retained. `main` continues directly
from thesis baseline `2021f17`; new commits add the research presentation,
reproduction workflow, and provenance. The environment and controller source
under `src/` is byte-for-byte unchanged from that baseline. The later private
`ikt` branch remains at `82553f6` and has not been merged into thesis `main`.

The private `public-simulator-release` maintenance branch was preserved
and pushed to the renamed origin. ECTLab was not modified: its public main
remains `1633f4b`, with the `ikt-2026` tag. The original checkout path remains
`/home/sky/HierarchicalEdgeSim`; its `origin` URL and branch tracking were updated.

## Transferred preparation material

The temporary standalone repository (GitHub ID 1458576089) was renamed to
`Sky-himself/vicinity-aware-autoscaling-preparation` to free the intended name.
Its useful README, citation metadata, experiment guide, campaign runner,
results figure, and summary tests were adapted to the integrated code layout.
The standalone package and external-simulator dependency were not introduced
into thesis main. New reference measurements were produced from the thesis
baseline itself, rather than relabeling the temporary project's output.

The owner deleted the extra GitHub repository after the saved API credential
could not perform that action. The repository without the `-preparation`
suffix is the preserved original research project.

## Validation and recovery

- Full consolidated suite with PyTorch: 343 tests passed.
- Fresh Python 3.12 installation without an external simulator dependency:
  installed successfully and ran the persistence quick-start scenario.
- Five-policy, two-service replay: matched the recorded drop/SLA/CPU values.
- Fresh clone: 78 engine/controller/config/trace/model/runner checksums verified.
- Ancestry checked: thesis baseline is retained; later IKT tip is not an
  ancestor of thesis main.
- ECTLab advertised main/tag refs checked and unchanged.

Recovery files are under
`/home/sky/HierarchicalEdgeSim-backups/2026-11-15/repository-consolidation/`:

- `original-repository.bundle`: original private history and maintenance refs.
- `preparation-repository.bundle`: complete temporary repository history.
- `github-before.json` and `github-renamed.json`: verified repository IDs/names.
- `preparation-deletion.json`: the earlier API deletion attempt response;
  final deletion was performed by the owner.
- `verification.json`: fresh-clone ancestry and checksum results.
- `preparation-checkout/`: archived local temporary checkout, with pushes disabled.
- `consolidated-verification/`: independent clone of the renamed original.

Both bundles were created before renaming; the temporary bundle was verified
before its checkout was archived. No original thesis source or Git history was
discarded.
