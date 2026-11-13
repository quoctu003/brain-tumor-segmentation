from dataclasses import replace
import hashlib
import json

import nibabel as nib
import numpy as np
import pytest

from app.config import settings


@pytest.fixture
def config(tmp_path):
    # Synthetic fixture: CI must not need or redistribute the user's MRI dataset.
    bundle = tmp_path / "synthetic-bundle"
    bundle.mkdir()
    rng = np.random.default_rng(42)
    for modality in ("t1n", "t1c", "t2w", "t2f"):
        image = nib.Nifti1Image(rng.uniform(1, 100, (12, 12, 12)).astype(np.float32), np.eye(4))
        image.header.set_xyzt_units("mm")
        nib.save(image, bundle / f"{modality}.nii.gz")
    mask = np.zeros((12, 12, 12), dtype=np.uint8)
    mask[2:8, 2:8, 2:8] = 2
    mask[3:7, 3:7, 3:7] = 1
    mask[4:6, 4:6, 4:6] = 3
    image = nib.Nifti1Image(mask, np.eye(4))
    image.header.set_xyzt_units("mm")
    nib.save(image, bundle / "segmentation.nii.gz")
    from app.imaging import region_volumes
    result = {"volumes_cm3": region_volumes(mask, np.eye(4)), "seconds": 0.01,
              "selected_epoch": 45, "training_epochs": 50, "model_state_id": "synthetic-test-only",
              "weights_sha256": "0" * 64, "provenance": {"kind": "recorded_inference", "recorded_at": "2000-01-01T00:00:00Z"}}
    (bundle / "result.json").write_text(json.dumps(result), "utf-8")
    manifest = {"format_version": 1, "title": "Synthetic test fixture", "source": "Synthetic test data",
                "source_case": "test-only", "recorded_at": "2000-01-01T00:00:00Z", "weights_sha256": "0" * 64,
                "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.iterdir()}}
    (bundle / "manifest.json").write_text(json.dumps(manifest), "utf-8")
    return replace(settings, storage=tmp_path / "storage", database_url="sqlite:///" + (tmp_path / "test.db").as_posix(), demo_dir=bundle)
