import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


def importer(tmp_path, monkeypatch, *, filename="unet_v2_best.pth"):
    path = Path(__file__).resolve().parents[2] / "scripts/prepare_model.py"
    spec = importlib.util.spec_from_file_location("model_importer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = tmp_path / "project"
    module.ROOT.mkdir()
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    weights = b"synthetic import test; not real model weights"
    (bundle / filename).write_bytes(weights)
    metadata = {"weights_sha256": hashlib.sha256(weights).hexdigest(),
                "protocol": {"total_epochs": 50}, "best_epoch": 45}
    (bundle / "model_metadata.json").write_text(json.dumps(metadata), "utf-8")
    monkeypatch.setattr(sys, "argv", [str(path), "--bundle", str(bundle)])
    return module, bundle, weights


@pytest.mark.parametrize("filename", ["unet_v1_demo.pth", "unet_v2_best.pth"])
def test_import_accepts_both_export_names_and_preserves_source(tmp_path, monkeypatch, filename):
    module, bundle, weights = importer(tmp_path, monkeypatch, filename=filename)
    module.main()
    assert (module.ROOT / "models/unet_v2_best.pth").read_bytes() == weights
    assert (bundle / filename).read_bytes() == weights
    assert not list((module.ROOT / "models").glob("import-*"))


def test_bad_checksum_does_not_overwrite_an_existing_model(tmp_path, monkeypatch):
    module, bundle, _ = importer(tmp_path, monkeypatch)
    destination = module.ROOT / "models"
    destination.mkdir()
    (destination / "unet_v2_best.pth").write_bytes(b"existing model")
    (bundle / "unet_v2_best.pth").write_bytes(b"corrupted")
    with pytest.raises(SystemExit, match="checksum mismatch"):
        module.main()
    assert (destination / "unet_v2_best.pth").read_bytes() == b"existing model"


def test_import_from_models_itself_does_not_fail_on_evaluation_copy(tmp_path, monkeypatch):
    module, bundle, _ = importer(tmp_path, monkeypatch)
    module.main()
    (module.ROOT / "models/evaluation.json").write_text("{}", "utf-8")
    monkeypatch.setattr(sys, "argv", ["prepare_model.py", "--bundle", str(module.ROOT / "models")])
    module.main()
    assert (module.ROOT / "models/evaluation.json").read_text("utf-8") == "{}"
