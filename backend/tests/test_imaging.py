import gzip
from dataclasses import replace

import nibabel as nib
import numpy as np
import pytest

from app.config import settings
from app.imaging import check_uncompressed_size, preprocess, region_volumes, validate_case


def test_volumes_use_affine_and_region_definitions():
    mask = np.array([[[0, 1, 2, 3]]], dtype=np.uint8)
    volumes = region_volumes(mask, np.diag([2, 3, 4, 1]))
    assert volumes == {"wt": 0.072, "tc": 0.048, "et": 0.024}


def test_gzip_limit_is_uncompressed(tmp_path):
    file = tmp_path / "oversized.nii.gz"
    file.write_bytes(gzip.compress(b"x" * 10000))
    with pytest.raises(ValueError, match="uncompressed"):
        check_uncompressed_size(file, 1024)


def test_normalization_preserves_background_and_modality_order(tmp_path):
    paths = {}
    array = np.arange(125, dtype=np.float32).reshape(5, 5, 5)
    for name in ("t1n", "t1c", "t2w", "t2f"):
        path = tmp_path / f"{name}.nii"
        nib.save(nib.Nifti1Image(array, np.eye(4)), path)
        paths[name] = path
    metadata = {"preprocessing": {"modalities": ["t1n", "t1c", "t2w", "t2f"], "clip_percentiles": [0.5, 99.5]}}
    image, reference = preprocess(paths, metadata)
    assert image.shape == (4, 5, 5, 5)
    assert np.all(image[:, 0, 0, 0] == 0)
    assert abs(image[0][array > 0].mean()) < 1e-6
    assert image[0][array > 0].std() == pytest.approx(1)
    np.testing.assert_array_equal(reference.affine, np.eye(4))


def test_reject_nan_and_voxel_limit(tmp_path):
    array = np.ones((4, 4, 4), np.float32)
    array[0, 0, 0] = np.nan
    file = tmp_path / "bad.nii"
    nib.save(nib.Nifti1Image(array, np.eye(4)), file)
    paths = {name: file for name in ("t1n", "t1c", "t2w", "t2f")}
    with pytest.raises(ValueError, match="NaN"):
        validate_case(paths, settings)
    with pytest.raises(ValueError, match="voxel limit"):
        validate_case(paths, replace(settings, max_voxels=8))


def test_unknown_units_on_any_modality_are_reported(tmp_path):
    paths = {}
    for name in ("t1n", "t1c", "t2w", "t2f"):
        image = nib.Nifti1Image(np.arange(64, dtype=np.float32).reshape(4, 4, 4), np.eye(4))
        image.header.set_xyzt_units("unknown" if name == "t2f" else "mm")
        paths[name] = tmp_path / f"{name}.nii"
        nib.save(image, paths[name])
    assert validate_case(paths, settings)["units_assumed_mm"] is True


def test_reject_complex_mri(tmp_path):
    file = tmp_path / "complex.nii"
    nib.save(nib.Nifti1Image(np.ones((4, 4, 4), np.complex64), np.eye(4)), file)
    with pytest.raises(ValueError, match="real-valued"):
        validate_case({name: file for name in ("t1n", "t1c", "t2w", "t2f")}, settings)


def test_reject_signal_that_becomes_constant_after_clipping(tmp_path):
    array = np.ones((12, 12, 12), np.float32)
    array[0, 0, 0] = 1000
    file = tmp_path / "outlier.nii"
    nib.save(nib.Nifti1Image(array, np.eye(4)), file)
    with pytest.raises(ValueError, match="after intensity clipping"):
        validate_case({name: file for name in ("t1n", "t1c", "t2w", "t2f")}, settings)
