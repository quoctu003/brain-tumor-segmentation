"""Integration smoke test using the REAL imported checkpoint on a synthetic volume.

Verifies loading/forward/export only. Does not measure segmentation accuracy.
"""
import json
import sys
import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.config import settings
from app.inference import ModelService


def main():
    torch.set_num_threads(4)
    service = ModelService(settings)
    service.load()
    if service.model is None:
        raise SystemExit(service.error)
    with tempfile.TemporaryDirectory(prefix="braintumor-smoke-") as directory:
        root = Path(directory)
        rng = np.random.default_rng(42)
        paths = {}
        for name in ("t1n", "t1c", "t2w", "t2f"):
            path = root / f"{name}.nii.gz"
            image = nib.Nifti1Image(rng.uniform(1, 200, (32, 32, 32)).astype(np.float32), np.eye(4))
            image.header.set_xyzt_units("mm")
            nib.save(image, path)
            paths[name] = path
        output = root / "segmentation.nii.gz"
        result = service.predict(paths, output, lambda value, stage: print(value, stage, flush=True))
        prediction = nib.load(output)
        assert prediction.shape == (32, 32, 32)
        assert set(np.unique(np.asarray(prediction.dataobj))) <= {0, 1, 2, 3}
        np.testing.assert_array_equal(prediction.affine, np.eye(4))
        print(json.dumps({"real_checkpoint_smoke": "passed", **result}, indent=2))


if __name__ == "__main__":
    main()
