import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "backend" / ".env", override=False)


def project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///storage/braintumor.db")
    storage: Path = project_path(os.getenv("STORAGE_DIR", "storage"))
    model_path: Path = project_path(os.getenv("MODEL_PATH", "models/unet_v2_best.pth"))
    metadata_path: Path = project_path(os.getenv("MODEL_METADATA_PATH", "models/model_metadata.json"))
    device: str = os.getenv("DEVICE", "auto")
    cors_origins: tuple[str, ...] = tuple(os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","))
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_MB", "128")) * 1024**2
    max_nifti_bytes: int = int(os.getenv("MAX_NIFTI_MB", "128")) * 1024**2
    max_voxels: int = int(os.getenv("MAX_VOXELS", "12000000"))
    max_pending_jobs: int = int(os.getenv("MAX_PENDING_JOBS", "4"))
    demo_dir: Path = project_path(os.getenv("DEMO_DIR", "demo"))
    frontend_dist: Path = project_path(os.getenv("FRONTEND_DIST", "frontend/dist"))


settings = Settings()
