import importlib.util
from pathlib import Path
import sys


def load_launcher():
    path = Path(__file__).resolve().parents[2] / "scripts/launch.py"
    spec = importlib.util.spec_from_file_location("local_launcher", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_fingerprint_tracks_application_and_public_assets_but_not_tests(tmp_path):
    launcher = load_launcher()
    launcher.ROOT = tmp_path
    frontend = tmp_path / "frontend"
    (frontend / "src").mkdir(parents=True)
    (frontend / "public").mkdir()
    for name in ("package.json", "package-lock.json", "index.html", "vite.config.ts", "tsconfig.json"):
        (frontend / name).write_text("initial")
    (frontend / "src/App.tsx").write_text("app")
    original = launcher.source_hash()
    (frontend / "src/App.test.tsx").write_text("test")
    assert launcher.source_hash() == original
    (frontend / "public/preview.png").write_bytes(b"asset")
    with_asset = launcher.source_hash()
    assert with_asset != original
    (frontend / "public/preview.png").write_bytes(b"updated")
    assert launcher.source_hash() != with_asset


def test_prepare_only_builds_even_when_the_application_is_running(monkeypatch):
    launcher = load_launcher()
    calls = []
    monkeypatch.setattr(sys, "argv", ["launch.py", "--prepare-only"])
    monkeypatch.setattr(launcher, "prepare", lambda: calls.append("prepare"))
    monkeypatch.setattr(launcher, "ensure_environment", lambda: None)
    def must_not_contact_server(*args, **kwargs):
        raise AssertionError("Preparing a build must not depend on the server or its port")
    monkeypatch.setattr(launcher, "health", must_not_contact_server)
    monkeypatch.setattr(launcher, "lock_workspace", must_not_contact_server)
    launcher.main()
    assert calls == ["prepare"]


def test_dependency_check_rejects_installed_but_incompatible_versions(monkeypatch, tmp_path):
    launcher = load_launcher()
    launcher.ROOT = tmp_path
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend/requirements.txt").write_text("# comment\nnumpy==2.2.6\ntorch==2.13.0\n")
    versions = {"numpy": "1.26.4", "torch": "2.13.0+cpu"}
    monkeypatch.setattr(launcher.importlib.metadata, "version", versions.__getitem__)
    assert launcher.missing_packages() == ["numpy==2.2.6"]


def test_environment_reentry_preserves_options_before_taking_any_lock(monkeypatch, tmp_path):
    launcher = load_launcher()
    launcher.ROOT = tmp_path
    monkeypatch.setattr(sys, "argv", ["launch.py", "--verify", "--port", "8095"])
    calls = []
    monkeypatch.setattr(launcher, "run", lambda command: calls.append(command))
    monkeypatch.setattr(launcher.subprocess, "call", lambda command: calls.append(command) or 0)
    monkeypatch.setattr(launcher, "lock_workspace", lambda *args: (_ for _ in ()).throw(AssertionError("Lock acquired before reentry")))
    import pytest
    with pytest.raises(SystemExit) as result:
        launcher.main()
    assert result.value.code == 0
    assert calls[0][-2:] == ["venv", str(tmp_path / ".venv")]
    assert calls[1][-3:] == ["--verify", "--port", "8095"]
