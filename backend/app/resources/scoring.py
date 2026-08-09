"""Resource state normalisation and configurable classification."""

from dataclasses import dataclass
from typing import Literal

from app.core.config import Settings, get_settings

ResourceLevel = Literal["critical", "low", "moderate", "high"]


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def calculate_resource_score(
    available_memory_mb: float,
    total_memory_mb: float,
    cpu_percent: float,
    battery_percent: float | None,
    network_available: bool,
    network_quality: float | None,
    settings: Settings | None = None,
) -> float:
    """Weight memory, CPU availability, battery, and network capacity."""
    memory_score = clamp(available_memory_mb / total_memory_mb) if total_memory_mb > 0 else 0.0
    cpu_score = clamp(1.0 - cpu_percent / 100.0)
    battery_score = clamp(battery_percent / 100.0) if battery_percent is not None else 0.5
    network_score = (
        clamp(network_quality)
        if network_available and network_quality is not None
        else float(network_available)
    )
    configuration = settings or get_settings()
    return clamp(
        configuration.resource_memory_weight * memory_score
        + configuration.resource_cpu_weight * cpu_score
        + configuration.resource_battery_weight * battery_score
        + configuration.resource_network_weight * network_score
    )


def classify_resource_level(score: float, settings: Settings | None = None) -> ResourceLevel:
    """Classify a normalised score using the configured resource thresholds."""
    configuration = settings or get_settings()
    if score <= configuration.resource_critical_threshold:
        return "critical"
    if score <= configuration.resource_low_threshold:
        return "low"
    if score <= configuration.resource_moderate_threshold:
        return "moderate"
    return "high"


@dataclass(frozen=True)
class ResourceSnapshot:
    available_memory_mb: float
    total_memory_mb: float
    cpu_percent: float
    battery_percent: float | None
    battery_charging: bool | None
    network_available: bool
    network_quality: float | None
    offline: bool
    storage_available_mb: float
    inference_latency_ms: float
    score: float
    level: ResourceLevel


def snapshot_from_measurements(
    available_memory_mb: float,
    total_memory_mb: float,
    cpu_percent: float,
    battery_percent: float | None,
    battery_charging: bool | None,
    network_available: bool,
    network_quality: float | None,
    storage_available_mb: float,
    inference_latency_ms: float,
    settings: Settings | None = None,
) -> ResourceSnapshot:
    """Create a scored snapshot from observed or simulated measurements."""
    score = calculate_resource_score(
        available_memory_mb,
        total_memory_mb,
        cpu_percent,
        battery_percent,
        network_available,
        network_quality,
        settings,
    )
    return ResourceSnapshot(
        available_memory_mb,
        total_memory_mb,
        cpu_percent,
        battery_percent,
        battery_charging,
        network_available,
        network_quality,
        not network_available,
        storage_available_mb,
        inference_latency_ms,
        score,
        classify_resource_level(score, settings),
    )
