"""Pickle-backed session storage for the FastAPI facade."""

from __future__ import annotations

import os
import pickle
import uuid
from pathlib import Path
from typing import Any


def session_dir() -> Path:
    path = Path(os.environ.get("GROWME_SESSION_DIR", ".growme_sessions"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def new_session_id() -> str:
    session_id = str(uuid.uuid4())
    save(session_id, {})
    return session_id


def path_for(session_id: str) -> Path:
    return session_dir() / f"{session_id}.pkl"


def artifact_dir(session_id: str) -> Path:
    path = session_dir() / session_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def load(session_id: str) -> dict[str, Any]:
    path = path_for(session_id)
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return pickle.load(f)


def save(session_id: str, data: dict[str, Any]) -> None:
    with path_for(session_id).open("wb") as f:
        pickle.dump(data, f)


def update(session_id: str, key: str, value: Any) -> dict[str, Any]:
    data = load(session_id)
    data[key] = value
    save(session_id, data)
    return data


def update_many(session_id: str, values: dict[str, Any]) -> dict[str, Any]:
    data = load(session_id)
    data.update(values)
    save(session_id, data)
    return data
