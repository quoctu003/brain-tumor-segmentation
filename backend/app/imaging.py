"""NIfTI contract matching the V2 training notebook; no registration or resampling."""
import gzip
from pathlib import Path

import nibabel as nib
import numpy as np

from .config import Settings

MODALITIES = ("t1n", "t1c", "t2w", "t2f")


def check_uncompressed_size(path: Path, limit: int):
    # Bound decompression before nibabel allocates an array.
    opener = gzip.open if path.name.endswith(".gz") else open
    total = 0
    with opener(path, "rb") as stream:
        while chunk := stream.read(1024 * 1024):
            total += len(chunk)
            if total > limit:
                raise ValueError("NIfTI exceeds the uncompressed size limit")


def validate_case(paths: dict[str, Path], config: Settings) -> dict:
    reference = None
    units_assumed_mm = False
    for name in MODALITIES:
        path = paths[name]
        check_uncompressed_size(path, config.max_nifti_bytes)
        # Avoid memory-mapped file handles surviving a validation exception on Windows.
        nii = nib.load(path, mmap=False)
        if nii.get_data_dtype().kind not in "iuf":
            raise ValueError(f"{name}: expected real-valued scalar MRI intensities")
        if len(nii.shape) != 3 or any(n <= 0 for n in nii.shape) or np.prod(nii.shape, dtype=np.int64) > config.max_voxels:
            raise ValueError(f"{name}: expected a 3D volume within the voxel limit")
        affine = np.asarray(nii.affine)
        if not np.isfinite(affine).all() or abs(np.linalg.det(affine[:3, :3])) < 1e-8:
            raise ValueError(f"{name}: invalid voxel-to-world affine")
        spatial_units = nii.header.get_xyzt_units()[0]
        units_assumed_mm |= spatial_units == "unknown"
        if spatial_units not in ("mm", "unknown"):
            raise ValueError(f"{name}: spatial units must be millimeters")
        if reference is None:
            reference = nii
        elif nii.shape != reference.shape or not np.allclose(nii.affine, reference.affine, rtol=0, atol=1e-4):
            raise ValueError(f"{name}: all four MRI volumes must share shape and affine; register them first")
        array = np.asarray(nii.dataobj, dtype=np.float32)
        if not np.isfinite(array).all():
            raise ValueError(f"{name}: MRI contains NaN or infinity")
        foreground = array[array > 0]
        if foreground.size == 0 or float(foreground.std(dtype=np.float64)) <= 1e-6:
            raise ValueError(f"{name}: empty or constant MRI signal")
        low, high = np.percentile(foreground, [0.5, 99.5])
        if float(np.clip(foreground, low, high).std(dtype=np.float64)) <= 1e-6:
            raise ValueError(f"{name}: near-zero variance after intensity clipping")
    return {"shape": list(reference.shape), "spacing_mm": nib.affines.voxel_sizes(reference.affine).tolist(),
            "affine": reference.affine.tolist(), "orientation": list(nib.aff2axcodes(reference.affine)),
            "units_assumed_mm": units_assumed_mm}


def preprocess(paths: dict[str, Path], metadata: dict):
    channels = []
    for name in metadata["preprocessing"]["modalities"]:
        nii = nib.load(paths[name], mmap=False)
        array = np.asarray(nii.dataobj, dtype=np.float32)
        brain = array > 0
        low, high = np.percentile(array[brain], metadata["preprocessing"]["clip_percentiles"])
        array = np.clip(array, low, high)
        std = float(array[brain].std())
        if std <= 1e-6:
            raise ValueError(f"{name}: near-zero variance after intensity clipping")
        array = (array - float(array[brain].mean())) / std
        array[~brain] = 0
        channels.append(array.astype(np.float32, copy=False))
    return np.stack(channels), nib.load(paths["t1n"], mmap=False)


def region_volumes(mask: np.ndarray, affine: np.ndarray) -> dict[str, float]:
    voxel_cm3 = abs(float(np.linalg.det(affine[:3, :3]))) / 1000
    return {name: round(float(region.sum()) * voxel_cm3, 4) for name, region in
            (("wt", mask > 0), ("tc", np.isin(mask, [1, 3])), ("et", mask == 3))}
