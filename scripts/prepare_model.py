"""Import verified V2 inference weights; never change the source training artifacts."""
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=ROOT.parent / "runs_v2/unet_v2_resumable_001/demo_bundle")
    args = parser.parse_args()
    source = args.bundle.resolve()
    if not (source / "model_metadata.json").is_file():
        parser.error("Bundle must contain model_metadata.json. Download the inference bundle from the Drive link in README.md, then pass --bundle <extracted-folder>.")
    metadata = json.loads((source / "model_metadata.json").read_text("utf-8"))
    candidates = [source / name for name in ("unet_v1_demo.pth", "unet_v2_best.pth") if (source / name).is_file()]
    weights = None
    for candidate in candidates:
        with candidate.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest == metadata.get("weights_sha256"):
            weights = candidate
            break
    if not candidates:
        parser.error("Bundle must contain unet_v1_demo.pth or unet_v2_best.pth; a raw training/resume checkpoint cannot be imported directly.")
    if weights is None:
        raise SystemExit("Source checksum mismatch. No files imported.")
    if metadata["protocol"]["total_epochs"] != 50:
        raise SystemExit("Expected the 50-epoch V2 experiment.")
    destination = ROOT / "models"
    destination.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="import-", dir=destination) as folder:
        staging = Path(folder)
        temporary = staging / "unet_v2_best.pth"
        shutil.copyfile(weights, temporary)
        with temporary.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                raise SystemExit("Copied checkpoint failed verification.")
        (staging / "model_metadata.json").write_text(json.dumps(metadata, indent=2), "utf-8")
        if (source / "evaluation.json").is_file():
            shutil.copyfile(source / "evaluation.json", staging / "evaluation.json")
        for path in staging.iterdir():
            path.replace(destination / path.name)
    print(json.dumps({"imported": str(destination), "training_epochs": 50, "selected_epoch": metadata["best_epoch"],
                      "sha256": digest, "test_dice_mean": metadata.get("test", {}).get("dice_mean")}, indent=2))


if __name__ == "__main__":
    main()
