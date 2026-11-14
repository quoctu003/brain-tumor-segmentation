"""Package a runnable local release without environments, secrets or user cases."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from launch import ROOT, source_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "releases/BrainTumorAI-1.1.0.zip")
    args = parser.parse_args()
    destination = args.output.resolve()
    stamp = ROOT / "frontend/dist/.source-hash"
    if not stamp.is_file() or stamp.read_text().strip() != source_hash():
        raise SystemExit("Prepare the current interface first: python scripts/launch.py --prepare-only")
    metadata = json.loads((ROOT / "models/model_metadata.json").read_text("utf-8"))
    with (ROOT / "models/unet_v2_best.pth").open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != metadata["weights_sha256"]:
            raise SystemExit("Model checksum mismatch; no release created.")
    files = []
    folders = ("backend", "scripts", "demo", "notebooks", "frontend/src", "frontend/public", "frontend/e2e", "frontend/dist", ".github", ".vscode")
    excluded = {"__pycache__", ".pytest_cache", "node_modules", "test-results", "playwright-report"}
    for folder in folders:
        files.extend(path for path in (ROOT / folder).rglob("*")
                     if path.is_file() and not excluded.intersection(path.relative_to(ROOT).parts)
                     and (not path.name.startswith(".env") or path.name == ".env.example")
                     and path.suffix not in (".pyc", ".db", ".sqlite", ".sqlite3", ".log", ".tmp"))
    names = ("DEMO_BRAINTUMOR.cmd", "START_BRAINTUMOR.cmd", "START_POSTGRES_DEMO.cmd", "README.md", "compose.yaml", "pytest.ini", ".gitignore", ".dockerignore", ".gitattributes",
             "frontend/package.json", "frontend/package-lock.json", "frontend/index.html", "frontend/tsconfig.json", "frontend/vite.config.ts",
             "frontend/playwright.config.ts", "frontend/Dockerfile", "frontend/nginx.conf", "models/.gitkeep", "models/unet_v2_best.pth", "models/model_metadata.json", "models/evaluation.json")
    files.extend(ROOT / name for name in names if (ROOT / name).is_file())
    if destination.exists():
        raise SystemExit(f"Release already exists: {destination}. Choose a new --output path.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    hashes = {}
    try:
        with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(set(files)):
                if not path.resolve().is_relative_to(ROOT):
                    raise ValueError("A release file resolves outside the project")
                name = path.relative_to(ROOT).as_posix()
                archive.write(path, "BrainTumorAI/" + name)
                with path.open("rb") as stream:
                    hashes[name] = hashlib.file_digest(stream, "sha256").hexdigest()
            archive.writestr("BrainTumorAI/RELEASE_MANIFEST.json", json.dumps({"version": "1.1.0", "files_sha256": hashes}, indent=2))
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    print(json.dumps({"release": str(destination), "files": len(hashes), "size_mb": round(destination.stat().st_size / 1024**2, 2)}, indent=2))


if __name__ == "__main__":
    main()
