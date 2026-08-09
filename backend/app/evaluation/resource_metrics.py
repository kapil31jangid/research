"""Research metrics that normalise learning benefit by resource cost."""


def personalisation_retention_ratio(constrained: float, full: float) -> float:
    return constrained / full if full > 0 else 0.0


def learning_efficiency(learning_gain: float, energy_units: float) -> float:
    return learning_gain / energy_units if energy_units > 0 else 0.0


def bandwidth_efficiency(mastery_improvement: float, kilobytes: float) -> float:
    return mastery_improvement / kilobytes if kilobytes > 0 else 0.0


def resource_normalised_learning_utility(
    normalised_gain: float,
    latency_ms: float,
    memory_pressure: float,
    cpu_fraction: float,
    bandwidth_kb: float,
    weights: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 0.25),
    latency_reference_ms: float = 10.0,
    bandwidth_reference_kb: float = 1024.0,
) -> float:
    """Return gain divided by one plus a dimensionless bounded resource-cost index."""
    components = (
        min(max(latency_ms / latency_reference_ms, 0.0), 1.0),
        min(max(memory_pressure, 0.0), 1.0),
        min(max(cpu_fraction, 0.0), 1.0),
        min(max(bandwidth_kb / bandwidth_reference_kb, 0.0), 1.0),
    )
    cost_index = sum(weight * value for weight, value in zip(weights, components, strict=True))
    return normalised_gain / (1.0 + cost_index)
