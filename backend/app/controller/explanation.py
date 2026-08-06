"""Human-readable controller explanations suitable for API responses and research logs."""

from app.controller.policy import ControllerDecision, ControllerInput


def explain_decision(decision: ControllerDecision, state: ControllerInput) -> list[str]:
    """Convert deterministic controller evidence into concise learner-safe statements."""
    explanation = [decision.reason]
    explanation.append(f"Resource score is {state.resource.score:.2f} ({state.resource.level}).")
    if state.resource.offline:
        explanation.append("The device is offline, so only locally available content can be used.")
    if decision.rejected_paths:
        explanation.append(
            "Lower-priority matching paths were not selected: "
            + ", ".join(decision.rejected_paths)
            + "."
        )
    return explanation
