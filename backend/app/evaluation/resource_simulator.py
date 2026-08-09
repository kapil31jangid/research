"""Seeded resource snapshots for controlled resource-aware experiments."""

import numpy as np

from app.resources.scoring import ResourceSnapshot, snapshot_from_measurements

_PROFILES = {
    "high_end": (8000, 15, 90, True),
    "mid_range": (3000, 35, 65, True),
    "low_end": (500, 75, 25, True),
    "offline": (500, 70, 30, False),
    "mixed": (2000, 45, 55, True),
}


def simulate_resource(profile: str, rng: np.random.Generator, step: int = 0) -> ResourceSnapshot:
    memory, cpu, battery, online = _PROFILES.get(profile, _PROFILES["mixed"])
    if profile == "mixed" and step % 5 == 4:
        online = False
    total_memory_mb = 8192.0
    return snapshot_from_measurements(
        float(np.clip(memory + rng.normal(0, memory * 0.05), 64, total_memory_mb)),
        total_memory_mb,
        float(np.clip(cpu + rng.normal(0, 5), 0, 100)),
        float(np.clip(battery - step * 0.5, 1, 100)),
        False,
        online,
        0.8 if online else 0.0,
        4096,
        float(max(1, 10 + cpu / 10)),
    )
