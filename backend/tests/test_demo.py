import io
import json
import shutil
import zipfile
from dataclasses import replace

from fastapi.testclient import TestClient

from app.main import create_app
from app.demo import DEMO_ID
from test_api import FakeModel, wait_job


class RecordedOnlyModel:
    def load(self):
        pass

    def status(self):
        return {"ready": False, "device": "cpu", "error": "Test: model deliberately unavailable"}

    def predict(self, *args):
        raise AssertionError("Opening a recorded demo must never execute inference")


def test_demo_is_instant_idempotent_and_exports_consistent_provenance(config):
    with TestClient(create_app(config, RecordedOnlyModel())) as client:
        assert client.get("/api/demo").json()["available"] is True
        first = client.post("/api/demo")
        assert first.status_code == 200, first.text
        case = first.json()
        assert case["id"] == DEMO_ID
        assert case["geometry"]["demo"]["source"] == "Synthetic test data"
        job = case["latest_job"]
        assert job["status"] == "completed"
        assert job["result"]["provenance"]["kind"] == "recorded_inference"
        assert job["result"]["volumes_cm3"]["wt"] > 0
        assert client.post("/api/demo").json()["latest_job"]["id"] == job["id"]
        assert len(client.get("/api/cases").json()) == 1
        package = client.get(f"/api/jobs/{job['id']}/bundle")
        assert package.status_code == 200
        with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
            assert set(archive.namelist()) == {"segmentation.nii.gz", "report.pdf", "result.json", "README.txt"}
            result = json.loads(archive.read("result.json"))
            assert result["case_id"] == case["id"]
            assert result["job_id"] == job["id"]
            assert result["provenance"]["kind"] == "recorded_inference"
            assert archive.read("report.pdf").startswith(b"%PDF")
        # The cached package has the exact same content on subsequent downloads.
        assert client.get(f"/api/jobs/{job['id']}/bundle").content == package.content
        assert client.delete(f"/api/cases/{case['id']}").status_code == 204
        assert client.post("/api/demo").json()["latest_job"]["id"] != job["id"]
        assert (config.demo_dir / "segmentation.nii.gz").is_file()


def test_corrupt_demo_never_creates_a_case(config, tmp_path):
    bundle = tmp_path / "demo"
    shutil.copytree(config.demo_dir, bundle)
    (bundle / "t1n.nii.gz").write_bytes(b"corrupt")
    with TestClient(create_app(replace(config, demo_dir=bundle), RecordedOnlyModel())) as client:
        assert client.post("/api/demo").status_code == 503
        assert client.get("/api/cases").json() == []


def test_missing_demo_is_reported_without_breaking_application(config, tmp_path):
    with TestClient(create_app(replace(config, demo_dir=tmp_path / "absent"), RecordedOnlyModel())) as client:
        assert client.get("/api/demo").json()["available"] is False
        assert client.post("/api/demo").status_code == 503
        assert client.get("/api/health").status_code == 200


def test_rerunning_demo_keeps_both_predictions_and_records_live_origin(config):
    with TestClient(create_app(config, FakeModel())) as client:
        demo = client.post("/api/demo").json()
        recorded = demo["latest_job"]["id"]
        start = client.post(f"/api/cases/{DEMO_ID}/inference").json()
        assert wait_job(client, start["id"])["status"] == "completed"
        history = client.get(f"/api/cases/{DEMO_ID}/jobs").json()
        assert len(history) == 2
        assert history[0]["result"]["provenance"]["kind"] == "live_inference"
        assert history[1]["id"] == recorded
        assert client.get(f"/api/jobs/{recorded}/artifacts/mask").status_code == 200


def test_system_and_static_frontend_do_not_hide_api_errors(config, tmp_path):
    frontend = tmp_path / "frontend"
    (frontend / "assets").mkdir(parents=True)
    (frontend / "index.html").write_text("<html>BrainTumor</html>")
    (frontend / "assets/app.js").write_text("console.log('ready')")
    with TestClient(create_app(replace(config, frontend_dist=frontend), RecordedOnlyModel())) as client:
        assert "BrainTumor" in client.get("/").text
        assert client.get("/assets/app.js").status_code == 200
        assert client.get("/api/missing").status_code == 404
        assert client.get("/missing.js").status_code == 404
        assert client.get("/..%5cbackend%5capp%5cconfig.py").status_code == 404
        health = client.get("/api/health").json()
        assert health["application"] == "braintumor-ai"
        assert health["frontend_ready"] is True
        state = client.get("/api/system").json()
        assert state["cases"] == 0
        assert state["jobs"]["running"] == 0
        assert state["storage_free_gb"] > 0
        assert "torch" in state["runtime"]
