# Maintaining the public simulator release

The private repository remains the development source. `ikt` and the existing
thesis branches/history are retained. Release tooling lives on
`codex/public-simulator-release`; merge this branch into the development branch
when desired. No export changes either remote or pushes anything.

`manifest.json` explicitly selects simulator files and tests. It excludes the
thesis controllers, models, experiments, and internal documentation. Public-only
README, license, packaging, controller registry, reproduction script, and
citation metadata live under `overlay/`. A few tests of excluded campaigns are
removed by exact function name; stale exclusions fail rather than silently drift.

## Prepare an update (Linux/WSL)

Commit the approved private source and release-tooling changes first. The export
reads every file, including its manifest and overlays, from the selected commit.
Uncommitted source edits are never exported.

```bash
cd /home/sky/HierarchicalEdgeSim
python3 paper-release/export.py --revision HEAD --destination /home/sky/HierarchicalEdgeSim-public
cd /home/sky/HierarchicalEdgeSim-public
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,plot]'
python -m pytest -q
python examples/reproduce_paper.py --verify
python examples/plot_ikt_hierarchy.py
sha256sum -c release-files.sha256
git diff --check
git diff
git add -A
git commit -m 'Update simulator release'
```

First export initializes an independent repository on `main`, with only an
`ectlab` remote. It does not copy any private commits, branches, tags, remote
settings, or private commit IDs into public files. The private source commit is
recorded locally in the public checkout's `.git/paper-export.json`. Public file
integrity is recorded in `release-files.sha256`.

Subsequent exports require a clean, managed public checkout. They replace the
approved files and remove obsolete tracked files. Generated, ignored results
are retained. Maintain source changes and public overlays here; direct edits to
the public checkout will be replaced by a later export.

## One-time ECTLab migration

Run only after public validation passes and live authentication works. Inspect
the repository's actual default branch, branches, tags, branch protections,
forks, and outstanding pull requests first. Cached tracking references are not
proof of the current remote state.

Before changing ECTLab, fetch all live ECTLab heads and tags into a separate
backup namespace in the private repository, record the exact advertised refs,
and create and verify an external Git bundle containing those refs and the
private refs. Keep that backup outside the public checkout. Verify private
origin access and that thesis history is backed up there before migration.

Replace ECTLab `main` using `--force-with-lease=refs/heads/main:<verified-old-SHA>`
from the public checkout. Remove only the live thesis branches and tags audited
for deletion; use exact expected-SHA leases on those deletions too. Never use
`--mirror`, `--all`, or a blanket tag push. Set the GitHub default branch to
`main` if necessary. If protections reject the update, stop and resolve that
specific restriction rather than weakening protections automatically.

Verify the published tree and advertised refs with a fresh clone. Tag the
validated paper release `ikt-2026`, then push that specific tag. Subsequent
updates use ordinary `git push ectlab main` from the public checkout. The
configured push refspec is a default, not an access-control boundary.

History replacement removes public branch/tag references, not existing clones,
forks, or every cached GitHub object. Existing collaborators should re-clone.

## Local checks for the exporter

```bash
python -m pytest -q paper-release/tests
```

These cover export selection, excluded-controller checks, stale exclusions,
repeatability, and refusal to overwrite unsafe destinations.
