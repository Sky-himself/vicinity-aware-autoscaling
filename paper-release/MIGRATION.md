# Completed migration — 15 November 2026

ECTLab's public `main` now points to independent root commit
`1633f4bdf3aa4b5a1fad1410d2e8ea74fa507c10`. The annotated `ikt-2026` tag
points to the same commit. A fresh GitHub clone contains only that commit in
its advertised history and passes every checksum in `release-files.sha256`.

The atomic, expected-SHA-leased push replaced `main`, deleted the three old
public thesis branches and seven thesis tags, and added the paper tag.
Before migration the public repository had no forks or open pull requests;
its default branch was `main`, which was not protected. The private origin's
four branch tips and seven annotated tags were checked before and after and
remain unchanged. Nothing was pushed to private origin.

## Working copies and backups

- Private development repository: `/home/sky/HierarchicalEdgeSim`.
- Release tooling/refactor branch: `public-simulator-release`.
- Public publishing checkout: `/home/sky/HierarchicalEdgeSim-public`.
- External backup: `/home/sky/HierarchicalEdgeSim-backups/2026-11-15/before-public-migration.bundle`.
- Audited original refs: `/home/sky/HierarchicalEdgeSim-backups/2026-11-15/ectlab-refs.txt`.
- Independent verification clone: `/home/sky/HierarchicalEdgeSim-backups/2026-11-15/public-verification`.

The external bundle was verified and contains the complete original history.
Original ECTLab refs are also retained under the private repository's
`refs/archive/ectlab-20261115/` namespace. They are not in the public checkout.

The private repository's origin URLs are unchanged. Its ECTLab fetch URL is
unchanged; its ECTLab push URL is deliberately disabled. Two old local branches
that tracked ECTLab now track their matching private-origin branches. All local
thesis branch tips remain intact.

The public checkout uses HTTPS and a repository-local helper invoking the
existing Windows Git Credential Manager from WSL. No global credential settings
were changed. Its `.git/paper-export.json` records private source provenance,
and `.git/paper-migration.json` records the audited migration; neither file is
published.

## Validation

- Private suite before and after the shared-helper move: 336 passed, 8 skipped.
- Exporter checks: 6 passed.
- Independently installed public package on Python 3.12: 186 tests passed.
- Four paper scenarios: reproduced all rounded drop, timeout, mean response,
  and average allocated-core values.
- Each scenario rerun: byte-identical metric and action logs, with workload
  conservation over all 721 windows and 3,385,510 requests.
- Minimal, static, and vertical examples ran; both plotting scripts succeeded.
- Hierarchy figure visually inspected; exported-file checksums verified locally
  and in a fresh GitHub clone.

MIT licensing was explicitly selected by the user. Dataset provenance is
documented separately. Publication metadata describes the paper as submitted
and does not invent a DOI or acceptance status.

For subsequent updates, follow `README.md` in this directory. The one-time
`migrate.py` tool defaults to a dry run and refuses to run against changed live
refs; it is not the normal publishing command.
