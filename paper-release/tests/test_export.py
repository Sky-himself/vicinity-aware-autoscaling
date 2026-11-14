"""Boundary and reproducibility checks for the private release exporter."""
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

SPEC = importlib.util.spec_from_file_location("paper_export", Path(__file__).parents[1] / "export.py")
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)


@pytest.fixture
def source(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir()
    monkeypatch.setattr(exporter, "SOURCE", root)
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root)
    git("init", "-b", "main")
    git("config", "user.name", "Release Test")
    git("config", "user.email", "test@example.invalid")
    (root / "paper-release" / "overlay").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "configs").mkdir()
    (root / "src" / "public.py").write_text("VALUE = 1\n")
    (root / "secret.md").write_text("private research\n")
    (root / "configs" / "00-tiny.yaml").write_text("sim: {}\n")
    manifest = {"files": ["src/*.py"], "renames": {"configs/00-tiny.yaml": "configs/minimal.yaml"}, "omit_functions": {}}
    (root / "paper-release" / "manifest.json").write_text(json.dumps(manifest))
    (root / "paper-release" / "overlay" / "README.md").write_text("Public simulator\n")
    git("add", ".")
    git("commit", "-m", "source")
    return root, git


def test_export_uses_committed_files_and_allowlist(source):
    root, _ = source
    (root / "src" / "public.py").write_text("VALUE = 99\n")
    commit, first = exporter.build_payload("HEAD")
    assert first["src/public.py"] == b"VALUE = 1\n"
    assert "secret.md" not in first
    assert "paper-release/manifest.json" not in first
    assert first == exporter.build_payload(commit)[1]
    assert commit.encode() not in b"".join(first.values())


def test_fresh_export_has_no_private_history_and_refuses_dirty_update(source, tmp_path):
    root, _ = source
    target = tmp_path / "public"
    exporter.export("HEAD", target)
    assert (target / "README.md").is_file()
    assert not (target / "secret.md").exists()
    refs = subprocess.run(["git", "show-ref"], cwd=target, capture_output=True)
    assert refs.returncode == 1
    with pytest.raises(ValueError, match="checkout changes"):
        exporter.export("HEAD", target)
    with pytest.raises(ValueError, match="separate"):
        exporter.export("HEAD", root / "nested")


def test_export_updates_only_managed_clean_checkout(source, tmp_path):
    _, _ = source
    target = tmp_path / "public"
    exporter.export("HEAD", target)
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "public root"], cwd=target, check=True, capture_output=True)
    before = (target / "release-files.sha256").read_bytes()
    exporter.export("HEAD", target)
    assert before == (target / "release-files.sha256").read_bytes()
    assert not subprocess.check_output(["git", "status", "--porcelain"], cwd=target)


def test_refuses_unmanaged_directory(source, tmp_path):
    target = tmp_path / "unrelated"
    target.mkdir()
    (target / "keep.txt").write_text("keep")
    with pytest.raises(ValueError, match="Destination must"):
        exporter.export("HEAD", target)
    assert (target / "keep.txt").read_text() == "keep"


def test_excluded_controller_import_is_rejected(source):
    root, git = source
    (root / "src" / "public.py").write_text("from hierarchical_edge_sim.autoscaler.reactive_local import build\n")
    git("add", ".")
    git("commit", "-m", "bad import")
    with pytest.raises(ValueError, match="Excluded controller"):
        exporter.build_payload("HEAD")


def test_function_exclusions_include_decorators_and_fail_when_stale():
    data = b"@marker\ndef excluded():\n    pass\n\ndef retained():\n    pass\n"
    result = exporter.remove_functions(data, ["excluded"])
    assert b"marker" not in result and b"excluded" not in result
    assert b"retained" in result
    with pytest.raises(ValueError, match="Stale"):
        exporter.remove_functions(data, ["missing"])
