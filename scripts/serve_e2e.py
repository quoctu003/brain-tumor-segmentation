"""Disposable real backend for browser tests; never uses the user's case database."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main():
    with tempfile.TemporaryDirectory(prefix="braintumor-e2e-") as folder:
        storage = Path(folder)
        os.environ["STORAGE_DIR"] = str(storage)
        os.environ["DATABASE_URL"] = "sqlite:///" + (storage / "cases.db").as_posix()
        os.environ["DEVICE"] = "cpu"
        os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"
        import torch
        import uvicorn
        torch.set_num_threads(4)
        uvicorn.run("app.main:app", host="127.0.0.1", port=8086, log_level="warning")


if __name__ == "__main__":
    main()
