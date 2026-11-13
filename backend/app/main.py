import json
import logging
import shutil
import threading
import platform
import zipfile
from importlib.metadata import version as package_version
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, update
from sqlalchemy.orm import aliased
from starlette.concurrency import run_in_threadpool

from .config import Settings, settings
from .database import Base, Case, Job, create_database, utc_now
from .imaging import MODALITIES, validate_case
from .inference import ModelService
from .reports import make_pdf
from .schemas import CaseResponse, JobResponse
from . import __version__
from .demo import DEMO_ID, demo_info, verify_demo
from .runtime import storage_lock

logger = logging.getLogger("braintumor")


def save_upload(upload: UploadFile, path: Path, limit: int, modality: str):
    size = 0
    with path.open("wb") as target:
        while chunk := upload.file.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                raise HTTPException(413, f"{modality}: file exceeds upload limit")
            target.write(chunk)


def create_app(config: Settings = settings, model_service=None):
    engine, sessions = create_database(config)
    model = model_service or ModelService(config)
    scheduling = threading.Lock()

    @asynccontextmanager
    async def lifespan(app):
        config.storage.mkdir(parents=True, exist_ok=True)
        with storage_lock(config.storage):
            try:
                Base.metadata.create_all(engine)
                with sessions.begin() as db:
                    db.execute(update(Job).where(Job.status.in_(["queued", "running"])).values(
                        status="failed", stage="Interrupted", error="Server restarted. Start inference again.", finished_at=utc_now()))
                await run_in_threadpool(model.load)
                app.state.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="inference")
                try:
                    yield
                finally:
                    await run_in_threadpool(app.state.worker.shutdown, wait=True)
            finally:
                engine.dispose()

    app = FastAPI(title="BrainTumor AI", version=__version__, lifespan=lifespan,
                  description="Local MRI research workspace. One API process and one inference worker.")
    app.add_middleware(CORSMiddleware, allow_origins=list(config.cors_origins), allow_credentials=False,
                       allow_methods=["GET", "POST", "DELETE"], allow_headers=["Content-Type"])
    app.state.model = model

    def case_directory(case_id: str):
        return config.storage / "cases" / case_id

    def case_paths(case_id: str):
        directory = case_directory(case_id)
        paths = {}
        for name in MODALITIES:
            path = next((directory / (name + suffix) for suffix in (".nii", ".nii.gz")
                         if (directory / (name + suffix)).is_file()), None)
            if path is None:
                raise FileNotFoundError(f"MRI volume missing on disk: {name}")
            paths[name] = path
        return paths

    def case_response(db, case):
        job = db.scalar(select(Job).where(Job.case_id == case.id).order_by(Job.created_at.desc(), Job.id.desc()).limit(1))
        return CaseResponse(id=case.id, name=case.name, created_at=case.created_at, geometry=case.geometry,
                            latest_job=JobResponse.model_validate(job) if job else None)

    def must_case(db, case_id):
        case = db.get(Case, case_id)
        if case is None:
            raise HTTPException(404, "Case not found")
        return case

    def execute_job(job_id: str, case_id: str):
        def progress(value, stage):
            with sessions.begin() as db:
                db.execute(update(Job).where(Job.id == job_id).values(status="running", progress=value, stage=stage))
        output_dir = case_directory(case_id) / "results" / job_id
        try:
            progress(5, "Preparing model")
            result = model.predict(case_paths(case_id), output_dir / "segmentation.nii.gz", progress)
            result["provenance"] = {"kind": "live_inference", "note": "Inference executed by this application."}
            with sessions.begin() as db:
                job = db.get(Job, job_id)
                job.result = result
                case = db.get(Case, case_id)
                (output_dir / "report.pdf").write_bytes(make_pdf(case, job))
                (output_dir / "result.json").write_text(json.dumps({"case_id": case_id, "job_id": job_id, **result}, indent=2), "utf-8")
                job.status, job.progress, job.stage, job.finished_at = "completed", 100, "Completed", utc_now()
        except Exception:
            logger.exception("Inference failed for job %s", job_id)
            with sessions.begin() as db:
                db.execute(update(Job).where(Job.id == job_id).values(status="failed", stage="Failed", finished_at=utc_now(),
                         error="Inference failed. Check server logs, model compatibility and available memory."))

    @app.get("/api/health")
    def health():
        with sessions() as db:
            db.execute(select(1))
        return {"status": "ok", "application": "braintumor-ai", "version": __version__,
                "database": "connected", "model_ready": model.status()["ready"],
                "frontend_ready": (config.frontend_dist / "index.html").is_file()}

    @app.get("/api/system")
    def system_info():
        with sessions() as db:
            count = db.scalar(select(func.count()).select_from(Case))
            jobs = dict(db.execute(select(Job.status, func.count()).group_by(Job.status)).all())
        disk = shutil.disk_usage(config.storage)
        return {"version": __version__, "database": "connected", "database_engine": engine.dialect.name, "cases": count,
                "jobs": {status: jobs.get(status, 0) for status in ("queued", "running", "completed", "failed")},
                "queue_capacity": config.max_pending_jobs, "storage_free_gb": round(disk.free / 1024**3, 2),
                "model": model.status(), "demo": demo_info(config),
                "frontend_ready": (config.frontend_dist / "index.html").is_file(),
                "runtime": {"python": platform.python_version(), **{name: package_version(name) for name in ("fastapi", "torch", "monai")}},
                "limits": {"upload_mb": config.max_upload_bytes // 1024**2, "workers": 1, "mode": "local_research"}}

    @app.get("/api/demo")
    def get_demo_info():
        return demo_info(config)

    @app.post("/api/demo", response_model=CaseResponse)
    def open_demo():
        with scheduling, sessions.begin() as db:
            existing = db.get(Case, DEMO_ID)
            if existing is not None:
                try:
                    case_paths(DEMO_ID)
                except FileNotFoundError as exc:
                    raise HTTPException(409, "Demo files are missing. Delete the demo study and open it again.") from exc
                return case_response(db, existing)
            try:
                manifest, geometry, result = verify_demo(config)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                logger.warning("Demo bundle verification failed: %s", exc)
                raise HTTPException(503, "Demo bundle unavailable or invalid. Check demo/manifest.json and its files.") from exc
            directory = case_directory(DEMO_ID)
            # A previous interrupted import can leave files without a database row.
            directory.mkdir(parents=True, exist_ok=True)
            job_id = str(uuid4())
            output_dir = directory / "results" / job_id
            try:
                for modality in MODALITIES:
                    shutil.copyfile(config.demo_dir / (modality + ".nii.gz"), directory / (modality + ".nii.gz"))
                output_dir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(config.demo_dir / "segmentation.nii.gz", output_dir / "segmentation.nii.gz")
                case = Case(id=DEMO_ID, name=manifest["title"], geometry=geometry)
                db.add(case)
                db.flush()
                job = Job(id=job_id, case_id=DEMO_ID, status="completed", progress=100,
                          stage="Recorded demo imported", result=result, finished_at=utc_now())
                db.add(job)
                db.flush()
                (output_dir / "report.pdf").write_bytes(make_pdf(case, job))
                (output_dir / "result.json").write_text(json.dumps({"case_id": case.id, "job_id": job.id, **result}, indent=2), "utf-8")
                response = case_response(db, case)
            except Exception:
                logger.exception("Demo import failed")
                raise HTTPException(500, "Cannot import demo. Check available disk space and server logs.")
            return response

    @app.get("/api/model")
    def model_info():
        return model.status()

    @app.get("/api/cases", response_model=list[CaseResponse])
    def list_cases(limit: int = 50, offset: int = 0):
        if not 1 <= limit <= 100 or offset < 0:
            raise HTTPException(422, "Invalid pagination")
        with sessions() as db:
            # Fetch the latest job in the same query instead of one query per case.
            latest_id = (select(Job.id).where(Job.case_id == Case.id)
                         .order_by(Job.created_at.desc(), Job.id.desc()).limit(1).correlate(Case).scalar_subquery())
            latest = aliased(Job)
            rows = db.execute(select(Case, latest).outerjoin(latest, latest.id == latest_id)
                              .order_by(Case.created_at.desc(), Case.id.desc()).offset(offset).limit(limit))
            return [CaseResponse(id=case.id, name=case.name, created_at=case.created_at, geometry=case.geometry,
                                 latest_job=JobResponse.model_validate(job) if job else None) for case, job in rows]

    @app.get("/api/cases/{case_id}", response_model=CaseResponse)
    def get_case(case_id: str):
        with sessions() as db:
            return case_response(db, must_case(db, case_id))

    @app.post("/api/cases", response_model=CaseResponse, status_code=201)
    async def upload_case(name: Annotated[str, Form(min_length=1, max_length=120)],
                          t1n: Annotated[UploadFile, File()], t1c: Annotated[UploadFile, File()],
                          t2w: Annotated[UploadFile, File()], t2f: Annotated[UploadFile, File()]):
        case_id = str(uuid4())
        directory = case_directory(case_id)
        directory.mkdir(parents=True, exist_ok=False)
        uploads = dict(zip(MODALITIES, (t1n, t1c, t2w, t2f)))
        paths = {}
        try:
            display_name = name.strip()
            if not display_name:
                raise HTTPException(422, "Study name cannot be blank")
            for modality, upload in uploads.items():
                filename = (upload.filename or "").lower()
                suffix = ".nii.gz" if filename.endswith(".nii.gz") else ".nii" if filename.endswith(".nii") else None
                if suffix is None:
                    raise HTTPException(422, f"{modality}: select a .nii or .nii.gz file")
                path = directory / (modality + suffix)
                await run_in_threadpool(save_upload, upload, path, config.max_upload_bytes, modality)
                paths[modality] = path
            geometry = await run_in_threadpool(validate_case, paths, config)
            with sessions.begin() as db:
                case = Case(id=case_id, name=display_name, geometry=geometry)
                db.add(case)
                db.flush()
                response = case_response(db, case)
            return response
        except HTTPException:
            shutil.rmtree(directory)
            raise
        except (ValueError, OSError, EOFError) as exc:
            shutil.rmtree(directory)
            raise HTTPException(422, f"Invalid MRI: {str(exc)[:240]}") from exc
        except Exception:
            shutil.rmtree(directory)
            logger.exception("Case upload failed")
            raise HTTPException(422, "Cannot read MRI files. Verify the NIfTI files and try again.")
        finally:
            for upload in uploads.values():
                await upload.close()

    @app.get("/api/cases/{case_id}/volumes/{modality}")
    def get_volume(case_id: str, modality: str):
        with sessions() as db:
            must_case(db, case_id)
        if modality not in MODALITIES:
            raise HTTPException(404, "Unknown modality")
        directory = case_directory(case_id)
        path = next((directory / (modality + suffix) for suffix in (".nii", ".nii.gz")
                     if (directory / (modality + suffix)).is_file()), None)
        if path is None:
            raise HTTPException(404, "MRI volume missing on disk")
        return FileResponse(path, media_type="application/octet-stream", filename=path.name)

    @app.post("/api/cases/{case_id}/inference", response_model=JobResponse, status_code=202)
    def start_inference(case_id: str):
        if not model.status()["ready"]:
            raise HTTPException(503, "Model unavailable. Run scripts/prepare_model.py and restart the API.")
        with scheduling, sessions.begin() as db:
            must_case(db, case_id)
            active = db.scalar(select(Job).where(Job.case_id == case_id, Job.status.in_(["queued", "running"])))
            if active:
                return JobResponse.model_validate(active)
            pending = db.scalar(select(func.count()).select_from(Job).where(Job.status.in_(["queued", "running"])))
            if pending >= config.max_pending_jobs:
                raise HTTPException(429, "Inference queue is full. Try again after a job completes.")
            job = Job(id=str(uuid4()), case_id=case_id, status="queued", progress=0, stage="Waiting for inference")
            db.add(job)
            db.flush()
            response = JobResponse.model_validate(job)
        try:
            app.state.worker.submit(execute_job, job.id, case_id)
        except RuntimeError as exc:
            with sessions.begin() as db:
                db.execute(update(Job).where(Job.id == job.id).values(
                    status="failed", stage="Failed", finished_at=utc_now(), error="Inference worker unavailable. Try again."))
            raise HTTPException(503, "Inference worker unavailable. Try again.") from exc
        return response

    @app.get("/api/jobs/{job_id}", response_model=JobResponse)
    def get_job(job_id: str):
        with sessions() as db:
            job = db.get(Job, job_id)
            if job is None:
                raise HTTPException(404, "Job not found")
            return JobResponse.model_validate(job)

    @app.get("/api/cases/{case_id}/jobs", response_model=list[JobResponse])
    def case_jobs(case_id: str):
        with sessions() as db:
            must_case(db, case_id)
            return [JobResponse.model_validate(job) for job in db.scalars(
                select(Job).where(Job.case_id == case_id).order_by(Job.created_at.desc(), Job.id.desc()).limit(50))]

    @app.get("/api/jobs/{job_id}/bundle")
    def download_bundle(job_id: str):
        with sessions() as db:
            job = db.get(Job, job_id)
            if job is None:
                raise HTTPException(404, "Job not found")
            if job.status != "completed":
                raise HTTPException(409, "Results are not ready")
            directory = case_directory(job.case_id) / "results" / job.id
            names = ("segmentation.nii.gz", "report.pdf", "result.json")
            if not all((directory / name).is_file() for name in names):
                raise HTTPException(404, "Result files missing on disk")
            destination = directory / "results.zip"
            if not destination.is_file():
                temporary = directory / (str(uuid4()) + ".tmp")
                try:
                    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
                        for name in names:
                            archive.write(directory / name, name)
                        archive.writestr("README.txt", "BrainTumor AI research output.\nSee result.json for model provenance.\nWT, TC and ET overlap; do not sum their volumes.\nNot a clinical diagnosis.\n")
                    temporary.replace(destination)
                finally:
                    temporary.unlink(missing_ok=True)
            return FileResponse(destination, media_type="application/zip", filename=f"{job.case_id}_results.zip")

    @app.get("/api/jobs/{job_id}/artifacts/{artifact}")
    def download_artifact(job_id: str, artifact: str):
        choices = {"mask": ("segmentation.nii.gz", "application/octet-stream"),
                   "report": ("report.pdf", "application/pdf"), "json": ("result.json", "application/json")}
        if artifact not in choices:
            raise HTTPException(404, "Unknown artifact")
        with sessions() as db:
            job = db.get(Job, job_id)
            if job is None:
                raise HTTPException(404, "Job not found")
            if job.status != "completed":
                raise HTTPException(409, "Results are not ready")
            filename, media_type = choices[artifact]
            path = case_directory(job.case_id) / "results" / job.id / filename
        if not path.is_file():
            raise HTTPException(404, "Artifact missing on disk")
        return FileResponse(path, media_type=media_type, filename=f"{job.case_id}_{filename}")

    @app.delete("/api/cases/{case_id}", status_code=204)
    def delete_case(case_id: str):
        with scheduling, sessions.begin() as db:
            case = must_case(db, case_id)
            if db.scalar(select(Job).where(Job.case_id == case_id, Job.status.in_(["queued", "running"]))):
                raise HTTPException(409, "Wait for inference to finish before deleting this study")
            for job in db.scalars(select(Job).where(Job.case_id == case_id)):
                db.delete(job)
            db.flush()
            db.delete(case)
        directory = case_directory(case_id).resolve()
        root = (config.storage / "cases").resolve()
        if directory.parent != root:
            raise RuntimeError("Unexpected case storage path")
        shutil.rmtree(directory, ignore_errors=True)
        return Response(status_code=204)

    assets = config.frontend_dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path == "api" or path.startswith("api/"):
            raise HTTPException(404, "API endpoint not found")
        root = config.frontend_dist.resolve()
        requested = (root / path).resolve()
        if not requested.is_relative_to(root):
            raise HTTPException(404, "Not found")
        if requested.is_file():
            return FileResponse(requested)
        if path and Path(path).suffix:
            raise HTTPException(404, "Asset not found")
        index = root / "index.html"
        if not index.is_file():
            raise HTTPException(503, "Frontend build missing. Start the application with START_BRAINTUMOR.cmd.")
        return FileResponse(index, headers={"Cache-Control": "no-cache"})

    return app


app = create_app()
