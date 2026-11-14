"""Export approved files from one committed revision into a separate public repo.

Never pushes, copies Git history, or reads uncommitted source files.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

SOURCE = Path(__file__).resolve().parents[1]
PUBLIC_URL = "git@github.com:ECTLab/HierarchicalEdgeSim.git"


def git(*args: str, cwd: Path | None = None) -> bytes:
    return subprocess.check_output(["git", *args], cwd=SOURCE if cwd is None else cwd)


def remove_functions(data: bytes, names: list[str]) -> bytes:
    source = data.decode("utf-8")
    lines = source.splitlines(keepends=True)
    found = set()
    removed = set()
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            found.add(node.name)
            start = min([node.lineno, *[d.lineno for d in node.decorator_list]])
            removed.update(range(start - 1, node.end_lineno))
    if found != set(names):
        raise ValueError(f"Stale function exclusions: {set(names) - found}")
    return "".join(line for i, line in enumerate(lines) if i not in removed).encode()


def build_payload(revision: str) -> tuple[str, dict[str, bytes]]:
    commit = git("rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip()
    entries = git("ls-tree", "-r", "-z", commit).split(b"\0")
    tree = {}
    for entry in filter(None, entries):
        metadata, path = entry.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        tree[path.decode()] = (mode, kind, oid)

    def read(path: str) -> bytes:
        mode, kind, oid = tree[path]
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"Only regular files may be exported: {path}")
        return git("cat-file", "blob", oid)

    manifest = json.loads(read("paper-release/manifest.json"))
    payload = {}
    for pattern in manifest["files"]:
        matched = [p for p in tree if fnmatch.fnmatchcase(p, pattern)]
        if not matched:
            raise ValueError(f"Allowlist pattern matches nothing: {pattern}")
        payload.update({p: read(p) for p in matched})
    for old, new in manifest["renames"].items():
        payload[new] = read(old)
    for path, names in manifest["omit_functions"].items():
        payload[path] = remove_functions(payload[path], names)
    # Rename the minimal example consistently in the retained tests.
    for path in payload:
        if path.startswith("tests/"):
            payload[path] = payload[path].replace(b"00-tiny.yaml", b"minimal.yaml")
    payload["configs/minimal.yaml"] = payload["configs/minimal.yaml"].replace(
        b"# configs/00-tiny.yaml \xe2\x80\x94 Part A reference scenario (03-implementation-plan.md \xc2\xa711)",
        b"# Minimal deterministic single-service example."
    )
    prefix = "paper-release/overlay/"
    for path in tree:
        if path.startswith(prefix):
            payload[path[len(prefix):]] = read(path)

    forbidden = ("reactive_local", "proactive_auto_scaler", "proscale")
    for path, data in payload.items():
        rel = PurePosixPath(path)
        if rel.is_absolute() or ".." in rel.parts or ".git" in rel.parts:
            raise ValueError(f"Unsafe export path: {path}")
        if path.startswith("src/") and path.endswith(".py"):
            ast.parse(data)
            if any(f"autoscaler.{name}".encode() in data for name in forbidden):
                raise ValueError(f"Excluded controller referenced in {path}")
    # Public checksums support integrity checks without exposing private commit IDs.
    payload["release-files.sha256"] = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {path}\n" for path, data in sorted(payload.items())
    ).encode()
    return commit, payload


def export(revision: str, destination: Path) -> None:
    commit, payload = build_payload(revision)
    destination = destination.resolve()
    source = SOURCE.resolve()
    if destination == source or source in destination.parents or destination in source.parents:
        raise ValueError("Public checkout must be separate from the private repository")
    fresh = not destination.exists() or not any(destination.iterdir())
    if not fresh:
        if not (destination / ".git").is_dir():
            raise ValueError("Destination must be empty or an existing managed public checkout")
        if git("rev-parse", "--show-toplevel", cwd=destination).decode().strip() != str(destination):
            raise ValueError("Destination must be the repository root")
        if not (destination / ".git" / "paper-export.json").is_file():
            raise ValueError("Refusing to modify an unmanaged repository")
        if git("status", "--porcelain", "--untracked-files=all", cwd=destination).strip():
            raise ValueError("Commit or remove public checkout changes before exporting again")
        urls = git("remote", "-v", cwd=destination).decode()
        if any(PUBLIC_URL not in line for line in urls.splitlines()):
            raise ValueError("Public checkout contains an unexpected remote")
    for path in payload:
        target = destination / path
        if not target.resolve().is_relative_to(destination):
            raise ValueError(f"Export target escapes destination: {path}")
        if any(parent.is_symlink() for parent in [target, *target.parents] if parent != destination.parent):
            raise ValueError(f"Symlink in export path: {path}")
    if fresh:
        destination.mkdir(parents=True, exist_ok=True)
        git("init", "-b", "main", cwd=destination)
        git("remote", "add", "ectlab", PUBLIC_URL, cwd=destination)
        git("config", "remote.ectlab.push", "refs/heads/main:refs/heads/main", cwd=destination)
        git("config", "push.followTags", "false", cwd=destination)
        for key in ("user.name", "user.email"):
            git("config", key, git("config", key).decode().strip(), cwd=destination)
    # Delete only formerly tracked release files; preserve ignored run outputs.
    tracked = git("ls-files", "-z", cwd=destination).decode().split("\0")
    for path in filter(None, tracked):
        if path not in payload:
            target = destination / path
            if not target.resolve().is_relative_to(destination):
                raise ValueError(f"Deletion target escapes destination: {path}")
            target.unlink(missing_ok=True)
    for path, data in payload.items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    record = {"source_commit": commit, "file_count": len(payload)}
    (destination / ".git" / "paper-export.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"Exported {len(payload)} files from {commit} to {destination}")
    print("Review, validate, and commit this checkout. No remote was changed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True, help="Committed private source revision")
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    export(args.revision, args.destination)
