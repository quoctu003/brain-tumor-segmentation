"""Serve one local API process; stdin closes it when the launcher exits."""
import argparse
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main():
    print("Initializing local server runtime...", flush=True)
    import uvicorn
    # Import native ML libraries before starting a thread that reads stdin.
    # On Windows those libraries may inspect the standard input stream at import.
    print("Loading application dependencies...", flush=True)
    from app.main import app
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=args.port))
    print("Loading application and checkpoint...", flush=True)
    def monitor_launcher():
        # EOF also requests shutdown if the parent console is closed unexpectedly.
        sys.stdin.readline()
        server.should_exit = True
    threading.Thread(target=monitor_launcher, daemon=True, name="launcher-control").start()
    server.run()
    if not server.started:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
