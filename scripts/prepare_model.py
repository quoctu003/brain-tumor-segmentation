"""Import verified V2 inference weights; never change the source training artifacts."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, default=ROOT.parent / "runs_v2/unet_v2_resumable_001/demo_bundle")
    args = parser.parse_args()
    source = args.bundle.resolve()
    metadata = json.loads((source / "model_metadata.json").read_text("utf-8"))
    weights = source / "unet_v1_demo.pth"  # Original export filename; metadata identifies V2.
    with weights.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != metadata.get("weights_sha256"):
        raise SystemExit("Source checksum mismatch. No files imported.")
    if metadata["protocol"]["total_epochs"] != 50:
        raise SystemExit("Expected the 50-epoch V2 experiment.")
    destination = ROOT / "models"
    destination.mkdir(exist_ok=True)
    temporary = destination / "unet_v2_best.pth.tmp"
    shutil.copyfile(weights, temporary)
    with temporary.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
            temporary.unlink()
            raise SystemExit("Copied checkpoint failed verification.")
    temporary.replace(destination / "unet_v2_best.pth")
    (destination / "model_metadata.json").write_text(json.dumps(metadata, indent=2), "utf-8")
    for name in ("evaluation.json",):
        if (source / name).is_file():
            shutil.copyfile(source / name, destination / name)
    print(json.dumps({"imported": str(destination), "training_epochs": 50, "selected_epoch": metadata["best_epoch"],
                      "sha256": digest, "test_dice_mean": metadata.get("test", {}).get("dice_mean")}, indent=2))


if __name__ == "__main__":
    main()
