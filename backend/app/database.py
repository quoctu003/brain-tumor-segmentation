from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import Settings, project_path


def utc_now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    geometry: Mapped[dict] = mapped_column(JSON)


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    progress: Mapped[int] = mapped_column(default=0)
    stage: Mapped[str] = mapped_column(String(120), default="Waiting for inference")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)


def create_database(config: Settings):
    url = config.database_url
    if url.startswith("sqlite:///") and url != "sqlite:///:memory:":
        file = project_path(url.removeprefix("sqlite:///"))
        file.parent.mkdir(parents=True, exist_ok=True)
        url = "sqlite:///" + file.as_posix()
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
                           **({"poolclass": StaticPool} if url in ("sqlite:///:memory:", "sqlite://") else {}))
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def configure_sqlite(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=10000")
            connection.execute("PRAGMA journal_mode=WAL")
    return engine, sessionmaker(engine, expire_on_commit=False)
