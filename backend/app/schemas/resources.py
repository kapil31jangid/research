"""Typed resource-monitoring API schemas."""

from pydantic import BaseModel, Field, model_validator


class ResourceStateRead(BaseModel):
    available_memory_mb: float = Field(ge=0.0)
    total_memory_mb: float = Field(gt=0.0)
    cpu_percent: float = Field(ge=0.0, le=100.0)
    battery_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    battery_charging: bool | None
    network_available: bool
    network_quality: float | None = Field(default=None, ge=0.0, le=1.0)
    offline: bool
    storage_available_mb: float = Field(ge=0.0)
    inference_latency_ms: float = Field(ge=0.0)
    score: float = Field(ge=0.0, le=1.0)
    level: str


class ResourceSimulationRequest(BaseModel):
    available_memory_mb: float = Field(ge=0.0)
    total_memory_mb: float = Field(gt=0.0)
    cpu_percent: float = Field(ge=0.0, le=100.0)
    battery_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    battery_charging: bool | None = None
    network_available: bool = True
    network_quality: float | None = Field(default=None, ge=0.0, le=1.0)
    storage_available_mb: float = Field(default=1_000.0, ge=0.0)
    inference_latency_ms: float = Field(default=0.0, ge=0.0)

    @model_validator(mode="after")
    def require_network_quality_when_online(self) -> "ResourceSimulationRequest":
        if self.network_available and self.network_quality is None:
            self.network_quality = 1.0
        return self
