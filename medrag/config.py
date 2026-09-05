from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


COLLECTION_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    provider: str
    allowed_document_root: Path | None
    host: str
    port: int

    @classmethod
    def from_env(cls) -> "Settings":
        root = os.getenv("MEDRAG_ALLOWED_DOCUMENT_ROOT", "").strip()
        return cls(
            data_dir=Path(os.getenv("MEDRAG_DATA_DIR", "./data")).expanduser().resolve(),
            provider=os.getenv("MEDRAG_PROVIDER", "ollama").strip().lower(),
            allowed_document_root=Path(root).expanduser().resolve() if root else None,
            host=os.getenv("MEDRAG_HOST", "127.0.0.1"),
            port=int(os.getenv("MEDRAG_PORT", "8090")),
        )

    def collection_dir(self, collection_id: str) -> Path:
        if not COLLECTION_RE.fullmatch(collection_id):
            raise ValueError("collection_id must use 1-64 letters, numbers, underscores, or hyphens")
        path = (self.data_dir / collection_id).resolve()
        if self.data_dir != path and self.data_dir not in path.parents:
            raise ValueError("invalid collection path")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def validate_document_directory(self, value: str) -> Path:
        path = Path(value).expanduser().resolve()
        if not path.is_dir():
            raise ValueError(f"document directory does not exist: {path}")
        root = self.allowed_document_root
        if root and path != root and root not in path.parents:
            raise ValueError(f"document directory must be under {root}")
        return path

