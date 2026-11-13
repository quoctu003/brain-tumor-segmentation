"""Verify real MRI upload/inference/artifacts in disposable storage, without touching user cases.

Requires backend development dependencies. This checks operation, not model accuracy.
"""
import argparse
from dataclasses import replace
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, help="Save the verification summary and exported PDF")
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args()
    directory = args.case_dir.resolve(strict=True)
    import nibabel as nib
    import numpy as np
    import torch
    from fastapi.testclient import TestClient
    from app.config import settings
    from app.imaging import MODALITIES, region_volumes
    from app.main import create_app

    paths = {}
    for modality in MODALITIES:
        matches = [p for p in directory.iterdir() if p.is_file() and
                   any(p.name.lower().endswith(ending) for ending in
                       (f"-{modality}.nii.gz", f"-{modality}.nii", f"{modality}.nii.gz", f"{modality}.nii"))]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {modality} NIfTI file in {directory}")
        paths[modality] = matches[0]
    torch.set_num_threads(4)
    started = time.perf_counter()
    test_root = Path(os.getenv("LOCALAPPDATA", str(Path.home() / ".local/share"))) / "BrainTumorAI-tests"
    test_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="real-case-", dir=test_root) as temporary:
        storage = Path(temporary)
        config = replace(settings, storage=storage, database_url="sqlite:///" + (storage / "verify.db").as_posix(), device="cpu")
        with TestClient(create_app(config)) as client:
            state = client.get("/api/model").json()
            if not state["ready"]:
                raise RuntimeError(state["error"])
            files = {name: (path.name, path.read_bytes(), "application/octet-stream") for name, path in paths.items()}
            response = client.post("/api/cases", data={"name": directory.name}, files=files)
            assert response.status_code == 201, response.text
            case = response.json()
            response = client.post(f"/api/cases/{case['id']}/inference")
            assert response.status_code == 202, response.text
            job_id = response.json()["id"]
            deadline = time.monotonic() + args.timeout
            previous = None
            while time.monotonic() < deadline:
                job = client.get(f"/api/jobs/{job_id}").json()
                if job["stage"] != previous:
                    print(f"{job['progress']}% {job['stage']}", flush=True)
                    previous = job["stage"]
                if job["status"] in ("completed", "failed"):
                    break
                time.sleep(0.5)
            else:
                raise TimeoutError("Inference did not finish before the verification timeout")
            assert job["status"] == "completed", job
            assert job["result"]["provenance"]["kind"] == "live_inference"
            artifacts = {}
            for name in ("mask", "report", "json"):
                response = client.get(f"/api/jobs/{job_id}/artifacts/{name}")
                assert response.status_code == 200, response.text
                artifacts[name] = response.content
            assert artifacts["report"].startswith(b"%PDF")
            result = json.loads(artifacts["json"])
            assert result["job_id"] == job_id and result["case_id"] == case["id"]
            mask_path = storage / "downloaded-mask.nii.gz"
            mask_path.write_bytes(artifacts["mask"])
            mask_nii = nib.load(mask_path, mmap=False)
            mask = np.asarray(mask_nii.dataobj)
            assert list(mask.shape) == case["geometry"]["shape"]
            np.testing.assert_allclose(mask_nii.affine, case["geometry"]["affine"], rtol=0, atol=1e-4)
            assert set(np.unique(mask)) <= {0, 1, 2, 3}
            assert mask.dtype == np.uint8
            assert region_volumes(mask, mask_nii.affine) == result["volumes_cm3"]
            response = client.get(f"/api/jobs/{job_id}/bundle")
            assert response.status_code == 200, response.text
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                assert set(archive.namelist()) == {"segmentation.nii.gz", "report.pdf", "result.json", "README.txt"}
                for filename, name in (("segmentation.nii.gz", "mask"), ("report.pdf", "report"), ("result.json", "json")):
                    assert archive.read(filename) == artifacts[name]
            assert client.get(f"/api/cases/{case['id']}/jobs").json()[0]["id"] == job_id
        # Confirm that the isolated case and result survive a clean API restart.
        with TestClient(create_app(config)) as restarted:
            assert restarted.get(f"/api/jobs/{job_id}").json()["status"] == "completed"
            assert restarted.get(f"/api/jobs/{job_id}/artifacts/report").content == artifacts["report"]
    summary = {"passed": True, "case": directory.name, "device": "cpu", "shape": list(mask.shape),
               "labels_present": np.unique(mask).tolist(), "model_sha256": state["weights_sha256"],
               "inference_seconds": result["seconds"], "total_seconds": round(time.perf_counter() - started, 2),
               "volumes_cm3": result["volumes_cm3"], "provenance": result["provenance"],
               "checks": ["real model load", "upload", "live inference", "mask geometry/dtype/labels",
                          "mask-derived volumes", "PDF", "JSON", "ZIP contents", "job history", "restart persistence"],
               "accuracy_evaluated": False}
    if args.report_dir:
        args.report_dir.mkdir(parents=True, exist_ok=True)
        (args.report_dir / "verification.json").write_text(json.dumps(summary, indent=2), "utf-8")
        (args.report_dir / "report.pdf").write_bytes(artifacts["report"])
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
