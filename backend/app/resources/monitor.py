"""Safe local-device resource measurements with platform fallbacks."""

import shutil
import socket
import time

import psutil

from app.resources.scoring import (
    ResourceSnapshot,
    calculate_resource_score,
    classify_resource_level,
)


def network_available(timeout_seconds: float = 0.2) -> bool:
    """Perform a bounded connectivity probe; failures are safely treated as offline."""
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def current_resources() -> ResourceSnapshot:
    """Read available host measurements without assuming battery support."""
    start = time.perf_counter()
    memory = psutil.virtual_memory()
    battery = psutil.sensors_battery()
    disk = shutil.disk_usage(".")
    connected = network_available()
    cpu_percent = psutil.cpu_percent(interval=None)
    score = calculate_resource_score(
        available_memory_mb=memory.available / 1_000_000,
        total_memory_mb=memory.total / 1_000_000,
        cpu_percent=cpu_percent,
        battery_percent=battery.percent if battery else None,
        network_available=connected,
        network_quality=1.0 if connected else 0.0,
    )
    return ResourceSnapshot(
        available_memory_mb=memory.available / 1_000_000,
        total_memory_mb=memory.total / 1_000_000,
        cpu_percent=cpu_percent,
        battery_percent=battery.percent if battery else None,
        battery_charging=battery.power_plugged if battery else None,
        network_available=connected,
        network_quality=1.0 if connected else 0.0,
        offline=not connected,
        storage_available_mb=disk.free / 1_000_000,
        inference_latency_ms=(time.perf_counter() - start) * 1000,
        score=score,
        level=classify_resource_level(score),
    )
