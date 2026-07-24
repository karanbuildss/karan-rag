"""Compatibility entry point for teammates running setup from the backend folder."""

from pathlib import Path
from runpy import run_path

run_path(
    str(Path(__file__).resolve().parent.parent / "scripts" / "bootstrap_local_security.py"),
    run_name="__main__",
)
