"""Protect process-owned inference queues from sharing the same case storage."""
from contextlib import contextmanager
import os
from pathlib import Path


@contextmanager
def storage_lock(storage: Path):
    storage.mkdir(parents=True, exist_ok=True)
    handle = (storage / ".api.lock").open("a+b")
    try:
        handle.write(b"0")
        handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError("Another BrainTumor API is using this storage. Close the previous backend before starting this workspace.") from exc
        yield
    finally:
        handle.close()
