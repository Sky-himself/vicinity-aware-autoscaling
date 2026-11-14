"""One-time, leased ECTLab history migration from an independently validated checkout.

Requires an audited ref snapshot and verified external bundle. Dry-run by default.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

URL = "https://github.com/ECTLab/HierarchicalEdgeSim.git"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--backup-refs", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    checkout = args.checkout.resolve()

    def git(*command: str) -> str:
        return subprocess.check_output(["git", *command], cwd=checkout).decode().strip()

    if not (checkout / ".git" / "paper-export.json").is_file():
        raise ValueError("Expected an independently managed public checkout")
    if git("status", "--porcelain"):
        raise ValueError("Public checkout is not clean")
    if git("remote", "get-url", "ectlab") != URL:
        raise ValueError("Unexpected public remote")
    old_refs = {}
    prefix = "refs/archive/ectlab-20261115/"
    for line in args.backup_refs.read_text().splitlines():
        oid, archived = line.split()
        if not archived.startswith(prefix):
            raise ValueError(f"Unexpected backup ref: {archived}")
        ref = "refs/" + archived[len(prefix):]
        if not ref.startswith(("refs/heads/", "refs/tags/")):
            raise ValueError(f"Unexpected ref: {ref}")
        old_refs[ref] = oid
    if "refs/heads/main" not in old_refs:
        raise ValueError("Backup snapshot does not include main")
    subprocess.run(["git", "bundle", "verify", str(args.bundle.resolve())], cwd=checkout, check=True,
                   stdout=subprocess.DEVNULL)
    live = dict((ref, oid) for oid, ref in (line.split() for line in git("ls-remote", "--refs", "ectlab").splitlines()))
    if live != old_refs:
        raise ValueError("Live refs differ from the audited backup; inspect and back up again")
    if git("rev-list", "--count", "main") != "1":
        raise ValueError("Initial public release must have exactly one independent root commit")
    public_commit = git("rev-parse", "main")
    if public_commit in old_refs.values():
        raise ValueError("Public main is still a thesis commit")
    if git("rev-parse", "ikt-2026^{commit}") != public_commit:
        raise ValueError("Paper tag must point to the validated public main")
    push = ["push", "--atomic"]
    push.extend(f"--force-with-lease={ref}:{oid}" for ref, oid in sorted(old_refs.items()))
    push.extend(["--force-with-lease=refs/tags/ikt-2026:", "ectlab", "refs/heads/main:refs/heads/main",
                 "refs/tags/ikt-2026:refs/tags/ikt-2026"])
    push.extend(f":{ref}" for ref in sorted(old_refs) if ref != "refs/heads/main")
    if not args.publish:
        push.insert(1, "--dry-run")
    subprocess.run(["git", *push], cwd=checkout, check=True)
    if args.publish:
        payload = {"public_commit": public_commit, "old_refs": old_refs,
                   "bundle": str(args.bundle.resolve()), "tag": "ikt-2026"}
        (checkout / ".git" / "paper-migration.json").write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
