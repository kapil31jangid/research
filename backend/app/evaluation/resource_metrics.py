"""Research metrics that normalise learning benefit by resource cost."""


def personalisation_retention_ratio(constrained: float, full: float) -> float:
    return constrained / full if full > 0 else 0.0


def learning_efficiency(learning_gain: float, energy_units: float) -> float:
    return learning_gain / energy_units if energy_units > 0 else 0.0


def bandwidth_efficiency(mastery_improvement: float, kilobytes: float) -> float:
    return mastery_improvement / kilobytes if kilobytes > 0 else 0.0


def resource_normalised_learning_utility(
    learning_gain: float,
    latency: float,
    memory: float,
    energy: float,
    bandwidth: float,
    weights: tuple[float, float, float, float] = (1, 1, 1, 1),
) -> float:
    cost = sum(
        weight * value
        for weight, value in zip(weights, (latency, memory, energy, bandwidth), strict=True)
    )
    return learning_gain / cost if cost > 0 else 0.0
