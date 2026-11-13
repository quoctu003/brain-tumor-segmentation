"""Import a verified, previously recorded prediction for a local presentation."""
import hashlib
import json

import nibabel as nib
import numpy as np

from .config import Settings
from .imaging import MODALITIES, region_volumes, validate_case

DEMO_ID = "4fd6c610-1f9e-571b-bfbe-555e211594d5"
DEMO_FILES = {*(name + ".nii.gz" for name in MODALITIES), "segmentation.nii.gz", "result.json"}


def demo_info(config: Settings):
    try:
        manifest = json.loads((config.demo_dir / "manifest.json").read_text("utf-8"))
        available = all((config.demo_dir / name).is_file() for name in DEMO_FILES)
        return {"available": available, "title": manifest["title"], "source": manifest["source"],
                "kind": "recorded_inference", "recorded_at": manifest["recorded_at"],
                "note": "Recorded real-checkpoint prediction. Open instantly; rerun AI separately."}
    except (OSError, ValueError, KeyError, TypeError):
        return {"available": False, "kind": "recorded_inference", "note": "Demo bundle is missing or invalid."}


def verify_demo(config: Settings):
    manifest = json.loads((config.demo_dir / "manifest.json").read_text("utf-8"))
    if manifest.get("format_version") != 1 or set(manifest.get("files", {})) != DEMO_FILES:
        raise ValueError("Unsupported demo manifest")
    for filename, expected in manifest["files"].items():
        with (config.demo_dir / filename).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
                raise ValueError(f"Demo checksum mismatch: {filename}")
    paths = {name: config.demo_dir / (name + ".nii.gz") for name in MODALITIES}
    geometry = validate_case(paths, config)
    from .imaging import check_uncompressed_size
    mask_path = config.demo_dir / "segmentation.nii.gz"
    check_uncompressed_size(mask_path, config.max_nifti_bytes)
    mask_nii = nib.load(mask_path, mmap=False)
    if list(mask_nii.shape) != geometry["shape"] or not np.allclose(mask_nii.affine, geometry["affine"], rtol=0, atol=1e-4):
        raise ValueError("Demo mask geometry differs from MRI")
    mask = np.asarray(mask_nii.dataobj)
    if not np.isin(mask, [0, 1, 2, 3]).all():
        raise ValueError("Unsupported demo labels")
    result = json.loads((config.demo_dir / "result.json").read_text("utf-8"))
    if result["weights_sha256"] != manifest["weights_sha256"] or result["provenance"]["kind"] != "recorded_inference":
        raise ValueError("Demo prediction provenance mismatch")
    volumes = region_volumes(mask, mask_nii.affine)
    if any(abs(volumes[key] - result["volumes_cm3"][key]) > 0.001 for key in volumes):
        raise ValueError("Recorded volumes do not match the demo mask")
    geometry["demo"] = {"source": manifest["source"], "source_case": manifest["source_case"]}
    return manifest, geometry, result
