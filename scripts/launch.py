"""One entry point: prepare, serve the built UI + API, open the browser, stop cleanly.

Only Python's standard library is needed to start this launcher.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
STATE = Path(os.getenv("LOCALAPPDATA", str(Path.home() / ".local/share"))) / "BrainTumorAI"
FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def say(message):
    print(message, flush=True)


def health(url):
    try:
        with urllib.request.urlopen(url + "/api/health", timeout=2) as response:
            body = json.load(response)
            return body if body.get("application") == "braintumor-ai" else None
    except (OSError, ValueError, urllib.error.URLError):
        return None


def source_hash():
    frontend = ROOT / "frontend"
    paths = [frontend / name for name in ("package.json", "package-lock.json", "index.html", "vite.config.ts", "tsconfig.json")]
    paths.extend(path for path in (frontend / "src").rglob("*") if path.is_file() and ".test." not in path.name)
    paths.extend(path for path in (frontend / "public").rglob("*") if path.is_file())
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(frontend).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def verify_workspace(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        if "BrainTumor" not in response.read().decode("utf-8"):
            raise RuntimeError("The production interface did not return the expected page.")
    with urllib.request.urlopen(url + "/api/model", timeout=10) as response:
        if "ready" not in json.load(response):
            raise RuntimeError("Model status endpoint is unavailable.")
    say("Verification passed: production UI, API and model status are available.")


def run(command, *, cwd=ROOT):
    logs = STATE / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    with (logs / "setup.log").open("ab") as output:
        is_batch = os.name == "nt" and Path(command[0]).suffix.lower() in (".cmd", ".bat")
        result = subprocess.run(command, cwd=cwd, stdout=output, stderr=subprocess.STDOUT,
                                creationflags=FLAGS, shell=is_batch)
    if result.returncode:
        raise RuntimeError(f"Setup failed (exit {result.returncode}). See {logs / 'setup.log'}")


def missing_packages():
    required = ("fastapi", "uvicorn", "sqlalchemy", "python-multipart", "python-dotenv", "numpy", "scipy", "nibabel", "torch", "monai", "reportlab")
    missing = []
    for name in required:
        try:
            importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(name)
    return missing


def prepare():
    missing = missing_packages()
    if missing:
        say("[1/3] Preparing isolated Python environment (first run may take several minutes)...")
        venv_python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if Path(sys.prefix).resolve() == (ROOT / ".venv").resolve():
            run([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "backend/requirements.txt")])
        else:
            if not venv_python.is_file():
                run([sys.executable, "-m", "venv", str(ROOT / ".venv")])
            run([str(venv_python), "-m", "pip", "install", "-r", str(ROOT / "backend/requirements.txt")])
            # Continue under the environment just installed; preserve every CLI option.
            raise SystemExit(subprocess.call([str(venv_python), str(Path(__file__)), *sys.argv[1:]]))
    else:
        say("[1/3] Python dependencies ready.")
    build_lock = lock_workspace("build")
    if build_lock is None:
        raise RuntimeError("Another interface build is running. Wait for it to finish and try again.")
    try:
        prepare_frontend()
    finally:
        build_lock.close()


def prepare_frontend():
    digest = source_hash()
    stamp = ROOT / "frontend/dist/.source-hash"
    if not (stamp.parent / "index.html").is_file() or not stamp.is_file() or stamp.read_text().strip() != digest:
        npm = shutil.which("npm")
        node = shutil.which("node")
        if not npm or not node:
            raise RuntimeError("Node.js 22.12+ or 24 is required for the first build. Install Node.js, then open START_BRAINTUMOR.cmd again.")
        node_version = subprocess.check_output([node, "--version"], text=True, creationflags=FLAGS).strip().lstrip("v")
        major, minor, *_ = (int(part) for part in node_version.split("."))
        if major < 22 or (major == 22 and minor < 12):
            raise RuntimeError("Please install Node.js 22.12+ or 24 before building.")
        say("[2/3] Installing and building the interface (only when source changes)...")
        run([npm, "ci", "--no-audit", "--no-fund"], cwd=ROOT / "frontend")
        run([npm, "run", "build"], cwd=ROOT / "frontend")
        stamp.write_text(digest, encoding="utf-8")
    else:
        say("[2/3] Interface build ready.")


def lock_workspace(scope="launcher"):
    STATE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(str(ROOT).encode()).hexdigest()[:12]
    handle = (STATE / f"{scope}-{key}.lock").open("a+b")
    handle.seek(0)
    handle.write(b"0")
    handle.flush()
    handle.seek(0)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--demo", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--check", action="store_true", help="Print prerequisites without changing anything")
    parser.add_argument("--verify", action="store_true", help="Start, verify the UI/API, then shut down without opening a browser")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    if args.check:
        print(json.dumps({"python": sys.version.split()[0], "missing_packages": missing_packages(),
                          "node_available": bool(shutil.which("node")), "model_available": (ROOT / "models/unet_v2_best.pth").is_file(),
                          "demo_available": (ROOT / "demo/manifest.json").is_file(),
                          "frontend_available": (ROOT / "frontend/dist/index.html").is_file()}, indent=2))
        return
    if not (3, 11) <= sys.version_info[:2] <= (3, 13):
        raise RuntimeError("Use Python 3.11, 3.12 or 3.13 for this project.")
    if args.prepare_only:
        prepare()
        say("Preparation complete. Double-click START_BRAINTUMOR.cmd to open the app.")
        return
    url = f"http://127.0.0.1:{args.port}"
    browser_url = url
    say("\n  BRAINTUMOR AI | Local Research Workspace\n  ---------------------------------------")
    lock = lock_workspace()
    if lock is None:
        say("An application launch is already active. Waiting for it...")
        for _ in range(120):
            if health(url):
                if args.verify:
                    verify_workspace(url)
                if not args.no_browser and not args.verify:
                    webbrowser.open(browser_url)
                say("Application is already running: " + url)
                return
            lock = lock_workspace()
            if lock is not None:
                break
            time.sleep(1)
        if lock is None:
            raise RuntimeError("Another launcher is still preparing. Check its window and logs; no duplicate backend was started.")
    process = None
    try:
        existing = health(url)
        if existing and existing.get("frontend_ready"):
            if args.verify:
                verify_workspace(url)
            if not args.no_browser and not args.verify:
                webbrowser.open(browser_url)
            say("Application is already running: " + url)
            return
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", args.port)) == 0:
                raise RuntimeError(f"Port {args.port} is occupied. Close that application or run scripts/launch.py --port 8081.")
        prepare()
        logs = STATE / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        environment = os.environ.copy()
        storage = STATE / "storage"
        environment.setdefault("STORAGE_DIR", str(storage))
        environment.setdefault("DATABASE_URL", "sqlite:///" + (storage / "braintumor.db").as_posix())
        environment.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
        environment.setdefault("PYTHONUTF8", "1")
        say("[3/3] Starting API, loading the checkpoint and opening the workspace...")
        with (logs / "backend.log").open("ab") as output:
            process = subprocess.Popen([sys.executable, str(ROOT / "scripts/serve_local.py"), "--port", str(args.port)],
                                       cwd=ROOT / "backend", env=environment, stdout=output, stderr=subprocess.STDOUT,
                                       stdin=subprocess.PIPE, creationflags=FLAGS)
        for _ in range(240):
            state = health(url)
            if state:
                break
            if process.poll() is not None:
                raise RuntimeError(f"Backend exited. Read {logs / 'backend.log'}")
            time.sleep(1)
        else:
            raise RuntimeError(f"Startup timed out. Read {logs / 'backend.log'}")
        if not args.no_browser and not args.verify:
            webbrowser.open(browser_url)
        say(f"\n  READY: {url}\n  Add an MRI study from the home screen.\n  Logs: {logs}\n  Keep this window open. Press Ctrl+C to stop.\n")
        if not state.get("model_ready"):
            say("  Model unavailable. See System in the app before starting inference.")
        if args.verify:
            verify_workspace(url)
            say("Shutting down the verification server.")
            return
        process.wait()
        if process.returncode:
            raise RuntimeError(f"Backend stopped unexpectedly. See {logs / 'backend.log'}")
    except KeyboardInterrupt:
        say("\nStopping the local workspace...")
    finally:
        if process is not None and process.poll() is None:
            try:
                process.stdin.write(b"stop\n")
                process.stdin.flush()
                process.stdin.close()
            except (BrokenPipeError, OSError):
                pass
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                say("Shutdown exceeded 30 seconds; stopping the worker. Unfinished jobs will be marked failed on restart.")
                process.terminate()
                process.wait(timeout=10)
        lock.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        say(f"\nERROR: {exc}")
        raise SystemExit(1)
