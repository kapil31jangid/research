"""Current and simulated device-resource endpoints."""

from fastapi import APIRouter

from app.resources.monitor import current_resources
from app.resources.scoring import (
    ResourceSnapshot,
    calculate_resource_score,
    classify_resource_level,
)
from app.schemas.resources import ResourceSimulationRequest, ResourceStateRead

router = APIRouter(prefix="/resources", tags=["resources"])


def serialise(snapshot: ResourceSnapshot) -> ResourceStateRead:
    return ResourceStateRead(**snapshot.__dict__)


@router.get("/current", response_model=ResourceStateRead)
async def get_current_resources() -> ResourceStateRead:
    return serialise(current_resources())


@router.post("/simulate", response_model=ResourceStateRead)
async def simulate_resources(payload: ResourceSimulationRequest) -> ResourceStateRead:
    score = calculate_resource_score(
        available_memory_mb=payload.available_memory_mb,
        total_memory_mb=payload.total_memory_mb,
        cpu_percent=payload.cpu_percent,
        battery_percent=payload.battery_percent,
        network_available=payload.network_available,
        network_quality=payload.network_quality,
    )
    return serialise(
        ResourceSnapshot(
            available_memory_mb=payload.available_memory_mb,
            total_memory_mb=payload.total_memory_mb,
            cpu_percent=payload.cpu_percent,
            battery_percent=payload.battery_percent,
            battery_charging=payload.battery_charging,
            network_available=payload.network_available,
            network_quality=payload.network_quality,
            offline=not payload.network_available,
            storage_available_mb=payload.storage_available_mb,
            inference_latency_ms=payload.inference_latency_ms,
            score=score,
            level=classify_resource_level(score),
        )
    )
