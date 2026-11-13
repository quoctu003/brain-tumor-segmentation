import copy
import hashlib
import json
from dataclasses import replace
from unittest.mock import patch

import pytest

from app.inference import ModelService


@pytest.mark.parametrize("change,expected", [
    ("architecture", "architecture"),
    ("labels", "label contract"),
])
def test_reject_metadata_that_changes_the_verified_model_contract(config, tmp_path, change, expected):
    architecture = {"channels": [16, 32, 64, 128, 256], "strides": [2, 2, 2, 2],
                    "num_res_units": 2, "norm": "instance", "dropout": 0.2}
    weights = tmp_path / "test-checkpoint.pth"
    weights.write_bytes(b"test-checkpoint")
    verified = {
        "weights_sha256": hashlib.sha256(weights.read_bytes()).hexdigest(),
        "best_state_id": "test-state",
        "protocol": {"total_epochs": 50, "architecture": architecture},
        "architecture": {"spatial_dims": 3, "in_channels": 4, "out_channels": 4, **copy.deepcopy(architecture)},
        "preprocessing": {"modalities": ["t1n", "t1c", "t2w", "t2f"], "resample": False,
                          "crop": False, "clip_percentiles": [0.5, 99.5], "foreground": "intensity > 0",
                          "normalize": "per-modality foreground z-score"},
        "labels": {"0": "background", "1": "NCR", "2": "ED", "3": "ET"},
        "test": {"dice_mean": 0.5},
    }
    metadata = copy.deepcopy(verified)
    if change == "architecture":
        # Changing stride can retain compatible parameter shapes while changing inference.
        metadata["architecture"]["strides"][0] = 1
    else:
        metadata["labels"]["3"] = "ED"
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps(metadata), "utf-8")
    checkpoint = {"metadata": {"best_state_id": verified["best_state_id"]},
                  "protocol": copy.deepcopy(verified["protocol"])}
    service = ModelService(replace(config, metadata_path=path, model_path=weights, device="cpu"))
    service.metadata = verified
    with patch("app.inference.torch.load", return_value=checkpoint):
        service.load()
    assert service.status()["ready"] is False
    assert expected in service.error
    assert service.status()["test"] is None
