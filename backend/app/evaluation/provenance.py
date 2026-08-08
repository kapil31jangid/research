"""Runtime and source provenance for reproducible experiments."""

import platform
import subprocess
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from os import cpu_count
from socket import gethostname

import psutil


def _package_versions() -> dict[str, str]:
    versions = {}
    for package in ("rapid-learn", "numpy", "pandas", "sqlalchemy", "scikit-learn"):
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = "unknown"
    return versions


def _git(*args: str) -> str:
    try:
        return (
            subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
            or "unknown"
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def collect_provenance(model_version: str | None = None) -> dict[str, object]:
    return {
        "git_commit_sha": _git("rev-parse", "HEAD"),
        "git_branch": _git("branch", "--show-current"),
        "repository_dirty_state": _git("status", "--porcelain") not in {"", "unknown"},
        "experiment_started_at": datetime.now(UTC).isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "hostname": gethostname(),
        "cpu_count": cpu_count() or 0,
        "total_memory_mb": round(psutil.virtual_memory().total / 1_048_576, 2),
        "package_versions": _package_versions(),
        "model_version": model_version or "unknown",
        "configuration_version": "1",
    }
