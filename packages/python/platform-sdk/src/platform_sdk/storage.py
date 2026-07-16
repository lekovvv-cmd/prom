from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import BinaryIO, Protocol


class ObjectStorage(Protocol):
    def put(self, key: str, source: BinaryIO) -> str: ...
    def get(self, key: str) -> BinaryIO: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...


class LocalFilesystemStorage:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        candidate = (self.root / key).resolve()
        if self.root != candidate and self.root not in candidate.parents:
            raise ValueError("Storage key escapes its module root")
        return candidate

    def put(self, key: str, source: BinaryIO) -> str:
        target = self._path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as destination:
            shutil.copyfileobj(source, destination)
        return hashlib.sha256(target.read_bytes()).hexdigest()

    def get(self, key: str) -> BinaryIO:
        return self._path(key).open("rb")

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

