"""Pickle-backed session state. One UUID per Streamlit session."""
from __future__ import annotations

import os
import pickle
import uuid
from pathlib import Path
from typing import Any

import streamlit as st


def _session_dir() -> Path:
    p = Path(os.environ.get("GROWME_SESSION_DIR", ".growme_sessions"))
    p.mkdir(exist_ok=True)
    return p


def session_uuid() -> str:
    if "session_uuid" not in st.session_state:
        st.session_state["session_uuid"] = str(uuid.uuid4())
    return st.session_state["session_uuid"]


def _path_for(uid: str) -> Path:
    return _session_dir() / f"{uid}.pkl"


def save(data: dict[str, Any]) -> None:
    with _path_for(session_uuid()).open("wb") as f:
        pickle.dump(data, f)


def load() -> dict[str, Any]:
    p = _path_for(session_uuid())
    if not p.exists():
        return {}
    with p.open("rb") as f:
        return pickle.load(f)


def update(key: str, value: Any) -> None:
    data = load()
    data[key] = value
    save(data)


def get(key: str, default: Any = None) -> Any:
    return load().get(key, default)


def set_session_uuid(uid: str) -> None:
    """Used by the assessment page to point at a wizard's session pickle."""
    st.session_state["session_uuid"] = uid


def reset_session() -> None:
    p = _path_for(session_uuid())
    if p.exists():
        p.unlink()
    for k in list(st.session_state.keys()):
        if k != "session_uuid":
            del st.session_state[k]
