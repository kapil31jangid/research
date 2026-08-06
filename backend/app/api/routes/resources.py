"""Current and simulated device-resource endpoints."""

from fastapi import APIRouter

from app.resources.monitor import current_resources
from app.resources.scoring import (
    ResourceSnapshot,
    snapshot_from_measurements,
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
    return serialise(
        snapshot_from_measurements(
            available_memory_mb=payload.available_memory_mb,
            total_memory_mb=payload.total_memory_mb,
            cpu_percent=payload.cpu_percent,
            battery_percent=payload.battery_percent,
            battery_charging=payload.battery_charging,
            network_available=payload.network_available,
            network_quality=payload.network_quality,
            storage_available_mb=payload.storage_available_mb,
            inference_latency_ms=payload.inference_latency_ms,
        )
    )
