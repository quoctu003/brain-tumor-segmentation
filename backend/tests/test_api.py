import time
import threading
from dataclasses import replace

import nibabel as nib
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import create_app
from app.database import Base, Case, Job, create_database


def nii_bytes(shape=(12, 12, 12), affine=None):
    rng = np.random.default_rng(42)
    image = nib.Nifti1Image(rng.uniform(1, 100, shape).astype(np.float32), np.eye(4) if affine is None else affine)
    image.header.set_xyzt_units("mm")
    return image.to_bytes()


class FakeModel:
    """Exercise API/job/artifact plumbing without pretending to evaluate trained weights."""
    def load(self):
        pass

    def status(self):
        return {"ready": True}

    def predict(self, paths, destination, progress):
        progress(50, "Test inference")
        reference = nib.load(paths["t1n"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        nib.save(nib.Nifti1Image(np.zeros(reference.shape, np.uint8), reference.affine), destination)
        return {"volumes_cm3": {"wt": 0, "tc": 0, "et": 0}, "seconds": 0.01, "selected_epoch": 45,
                "training_epochs": 50, "model_state_id": "test-only", "weights_sha256": "0" * 64}


@pytest.fixture
def client(config):
    with TestClient(create_app(config, FakeModel())) as client:
        yield client


def upload(client, override=None, name="Study A"):
    files = {key: (f"{key}.nii", nii_bytes(), "application/octet-stream") for key in ("t1n", "t1c", "t2w", "t2f")}
    files.update(override or {})
    return client.post("/api/cases", data={"name": name}, files=files)


def test_upload_infer_download_and_delete(client):
    response = upload(client)
    assert response.status_code == 201, response.text
    case = response.json()
    assert case["geometry"]["shape"] == [12, 12, 12]
    assert client.get(f"/api/cases/{case['id']}/volumes/t2f").content == nii_bytes()
    start = client.post(f"/api/cases/{case['id']}/inference")
    assert start.status_code == 202
    job_id = start.json()["id"]
    for _ in range(100):
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in ("completed", "failed"):
            break
        time.sleep(0.03)
    assert job["status"] == "completed", job
    assert client.get(f"/api/jobs/{job_id}/artifacts/report").content.startswith(b"%PDF")
    assert client.get(f"/api/jobs/{job_id}/artifacts/json").json()["case_id"] == case["id"]
    assert client.get(f"/api/jobs/{job_id}/artifacts/mask").status_code == 200
    assert client.get("/api/cases").json()[0]["latest_job"]["status"] == "completed"
    assert client.delete(f"/api/cases/{case['id']}").status_code == 204
    assert client.get(f"/api/cases/{case['id']}").status_code == 404


def test_reject_misaligned_and_clean_partial_files(client, config):
    response = upload(client, {"t2f": ("t2f.nii", nii_bytes(affine=np.diag([2, 1, 1, 1])), "application/octet-stream")})
    assert response.status_code == 422
    assert "affine" in response.json()["detail"]
    assert client.get("/api/cases").json() == []
    assert list((config.storage / "cases").iterdir()) == []


def test_never_use_user_filename_as_storage_path(client, config):
    response = upload(client, {"t1n": ("../../outside.nii", nii_bytes(), "application/octet-stream")})
    assert response.status_code == 201
    directory = config.storage / "cases" / response.json()["id"]
    assert (directory / "t1n.nii").is_file()
    assert not (config.storage / "outside.nii").exists()


@pytest.mark.parametrize("filename,content", [("scan.txt", b"bad"), ("scan.nii.gz", b"bad gzip"), ("scan.nii", b"bad nifti")])
def test_reject_invalid_uploads(client, filename, content):
    response = upload(client, {"t1n": (filename, content, "application/octet-stream")})
    assert response.status_code == 422


def test_upload_limit(config):
    with TestClient(create_app(replace(config, max_upload_bytes=10), FakeModel())) as client:
        assert upload(client).status_code == 413


def test_missing_files_and_unknown_ids(client):
    assert client.post("/api/cases", data={"name": "A"}).status_code == 422
    assert client.get("/api/cases/unknown").status_code == 404
    assert client.get("/api/jobs/unknown").status_code == 404
    assert client.get("/api/cases?limit=500").status_code == 422


def test_database_persists_across_restart(config):
    with TestClient(create_app(config, FakeModel())) as first:
        case_id = upload(first).json()["id"]
    with TestClient(create_app(config, FakeModel())) as second:
        assert second.get(f"/api/cases/{case_id}").status_code == 200


def wait_job(client, job_id):
    for _ in range(150):
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in ("completed", "failed"):
            return job
        time.sleep(0.02)
    pytest.fail("Inference did not finish")


def test_dates_include_utc_and_missing_volume_returns_404(client, config):
    case = upload(client).json()
    assert case["created_at"].endswith("Z")
    (config.storage / "cases" / case["id"] / "t2f.nii").unlink()
    assert client.get(f"/api/cases/{case['id']}/volumes/t2f").status_code == 404
    # A missing unrelated modality must not prevent downloading a healthy one.
    assert client.get(f"/api/cases/{case['id']}/volumes/t1n").status_code == 200


def test_queue_limits_duplicate_requests_and_delete_protection(config):
    release = threading.Event()

    class BlockingModel(FakeModel):
        def predict(self, paths, destination, progress):
            if not release.wait(10):
                raise RuntimeError("Test worker timed out")
            return super().predict(paths, destination, progress)

    with TestClient(create_app(replace(config, max_pending_jobs=1), BlockingModel())) as client:
        try:
            first, second = upload(client).json(), upload(client).json()
            job = client.post(f"/api/cases/{first['id']}/inference").json()
            assert client.post(f"/api/cases/{first['id']}/inference").json()["id"] == job["id"]
            assert client.post(f"/api/cases/{second['id']}/inference").status_code == 429
            assert client.delete(f"/api/cases/{first['id']}").status_code == 409
            assert client.get(f"/api/jobs/{job['id']}/artifacts/mask").status_code == 409
        finally:
            release.set()
        assert wait_job(client, job["id"])["status"] == "completed"


def test_failed_job_does_not_block_retry(config):
    class FailingOnceModel(FakeModel):
        failed = False

        def predict(self, paths, destination, progress):
            if not self.failed:
                self.failed = True
                raise RuntimeError("Synthetic failure")
            return super().predict(paths, destination, progress)

    with TestClient(create_app(config, FailingOnceModel())) as client:
        case = upload(client).json()
        first = client.post(f"/api/cases/{case['id']}/inference").json()
        assert wait_job(client, first["id"])["status"] == "failed"
        second = client.post(f"/api/cases/{case['id']}/inference").json()
        result = wait_job(client, second["id"])
        assert result["status"] == "completed"
        assert result["finished_at"].endswith("Z")
        assert client.get("/api/cases").json()[0]["latest_job"]["id"] == second["id"]


def test_restart_marks_interrupted_jobs_failed(config):
    engine, sessions = create_database(config)
    Base.metadata.create_all(engine)
    with sessions.begin() as db:
        db.add(Case(id="case", name="Interrupted study", geometry={}))
        db.flush()
        db.add(Job(id="job", case_id="case", status="running"))
    engine.dispose()
    with TestClient(create_app(config, FakeModel())) as client:
        job = client.get("/api/jobs/job").json()
        assert job["status"] == "failed"
        assert "restarted" in job["error"]


def test_rejected_worker_submission_is_not_left_queued(config, monkeypatch):
    app = create_app(config, FakeModel())
    with TestClient(app) as client:
        case = upload(client).json()
        def unavailable(*args, **kwargs):
            raise RuntimeError("Worker shut down")
        monkeypatch.setattr(app.state.worker, "submit", unavailable)
        assert client.post(f"/api/cases/{case['id']}/inference").status_code == 503
        assert client.get(f"/api/cases/{case['id']}").json()["latest_job"]["status"] == "failed"


def test_in_memory_database_is_shared_with_api_threads(config):
    with TestClient(create_app(replace(config, database_url="sqlite:///:memory:"), FakeModel())) as client:
        assert upload(client).status_code == 201
        assert len(client.get("/api/cases").json()) == 1


def test_blank_names_are_rejected_and_cleaned(client, config):
    assert upload(client, name="   ").status_code == 422
    assert list((config.storage / "cases").iterdir()) == []
